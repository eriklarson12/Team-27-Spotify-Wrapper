from collections import Counter

import requests
from django.conf import settings
from django.http import JsonResponse
import base64
import urllib.parse
from django.shortcuts import render, redirect


def index(request):
    """
    View for the home/landing page
    """
    return render(request, 'spotify_auth/index.html')


def spotify_login(request):
    # Spotify OAuth endpoint
    auth_url = "https://accounts.spotify.com/authorize"

    # Parameters for the OAuth URL
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": "user-read-private user-read-email user-top-read",  # Added user-top-read scope
    }
    # Redirect to Spotify's login page
    return redirect(f"{auth_url}?{urllib.parse.urlencode(params)}")


def spotify_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "Authorization code not provided."}, status=400)

    token_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(
        f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
    }
    response = requests.post(token_url, headers=headers, data=data)
    response_data = response.json()

    if "access_token" in response_data:
        access_token = response_data["access_token"]
        refresh_token = response_data.get("refresh_token")

        # Store both tokens in the session
        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token
        return redirect('profile')
    else:
        return JsonResponse({"error": "Failed to retrieve access token."}, status=400)


def refresh_access_token(session):
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        return None

    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}'.encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = requests.post(token_url, headers=headers, data=data)
    response_data = response.json()

    # Update session with new access token if successful
    if "access_token" in response_data:
        session['access_token'] = response_data["access_token"]
        return response_data["access_token"]
    return None


def profile(request):
    access_token = request.session.get('access_token')

    if not access_token:
        return redirect('spotify_login')

    profile_url = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Fetch profile data, refreshing token if needed
    profile_response = requests.get(profile_url, headers=headers)

    if profile_response.status_code == 403:
        # Attempt to refresh the access token
        access_token = refresh_access_token(request.session)
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
            profile_response = requests.get(profile_url, headers=headers)

    if profile_response.status_code != 200:
        return JsonResponse({"error": "Failed to retrieve profile data.", "details": profile_response.text},
                            status=profile_response.status_code)

    profile_data = profile_response.json()
    return render(request, 'spotify_auth/profile.html', {"profile": profile_data})


# Function to get top tracks
def get_top_tracks(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return []

    url = "https://api.spotify.com/v1/me/top/tracks"
    headers = get_spotify_headers(access_token)
    params = {"limit": 5, "time_range": "medium_term"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return []

    tracks = response.json().get("items", [])
    return [(track["name"], track["preview_url"]) for track in tracks]


# Function to get top artists
def get_top_artists(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return []

    url = "https://api.spotify.com/v1/me/top/artists"
    headers = get_spotify_headers(access_token)
    params = {"limit": 5, "time_range": "medium_term"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return []

    artists = response.json().get("items", [])
    return [artist["name"] for artist in artists]


# Function to get top genre
def get_top_genre(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return "Unknown"

    url = "https://api.spotify.com/v1/me/top/artists"
    headers = get_spotify_headers(access_token)
    params = {"limit": 10, "time_range": "medium_term"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return "Unknown"

    artists = response.json().get("items", [])
    genres = [genre for artist in artists for genre in artist.get("genres", [])]
    top_genre = Counter(genres).most_common(1)
    return top_genre[0][0] if top_genre else "Unknown"


def get_personality_insights(request):
    from .gemini_client import GeminiClient

    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('spotify_login')

    # Initialize Gemini client
    gemini_client = GeminiClient()

    try:
        # Fetch top artists data
        top_artists_url = "https://api.spotify.com/v1/me/top/artists"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        params = {
            "limit": 20,  # Consistent with other views
            "time_range": "medium_term"
        }

        response = requests.get(top_artists_url, headers=headers, params=params)

        if response.status_code == 403:
            access_token = refresh_access_token(request.session)
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
                response = requests.get(top_artists_url, headers=headers, params=params)

        if response.status_code != 200:
            return JsonResponse({
                "error": "Failed to retrieve top artists.",
                "details": response.text
            }, status=response.status_code)

        artists_data = response.json().get('items', [])

        # Extract top artists names (take top 5 for personality insights)
        top_artists = [artist['name'] for artist in artists_data[:5]]

        # Collect all genres from all artists
        genres = []
        for artist in artists_data:
            genres.extend(artist.get('genres', []))

        # Get top 5 genres using Counter (consistent with get_top_genre)
        genre_counts = Counter(genres)
        top_genres = [genre for genre, _ in genre_counts.most_common(5)]

        # Generate personality insights
        personality_insights = gemini_client.generate_personality_insights(
            top_genres=top_genres,
            top_artists=top_artists
        )

        # Return JSON if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'personality_insights': personality_insights,
                'top_artists': top_artists,
                'top_genres': top_genres
            })
        # print("Top Artists:", top_artists)
        # print("Top Genres:", top_genres)
        # print("Personality Insights:", personality_insights)

        # Otherwise render the full template
        return personality_insights

    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)

def get_top_artists2(access_token, time_range):
    url = 'https://api.spotify.com/v1/me/top/artists'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'limit': 50,
        'time_range': time_range  # Can be 'medium_term' or 'long_term'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return [artist['name'] for artist in data['items']]
    return []




# Function to get new artists discovered
def new_artists_discovered(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return 0

    url = "https://api.spotify.com/v1/me/top/artists"
    headers = get_spotify_headers(access_token)

    # Get short-term and long-term top artists
    short_term_response = requests.get(url, headers=headers, params={"time_range": "short_term"})
    long_term_response = requests.get(url, headers=headers, params={"time_range": "long_term"})

    if short_term_response.status_code != 200 or long_term_response.status_code != 200:
        return 0

    short_term_artists = {artist["name"] for artist in short_term_response.json().get("items", [])}
    long_term_artists = {artist["name"] for artist in long_term_response.json().get("items", [])}

    # New artists are those in short-term data but not in long-term data
    new_artists = short_term_artists - long_term_artists
    return len(new_artists)





def get_listening_time(request):
    access_token = request.session.get('access_token')

    if not access_token:
        return redirect('spotify_login')

    top_tracks_url = "https://api.spotify.com/v1/me/top/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Parameters for the API request - we just need the top track
    params = {
        "limit": 1,  # Only get the top track
        "time_range": "medium_term"
    }

    # Fetch top track data
    response = requests.get(top_tracks_url, headers=headers, params=params)

    if response.status_code == 403:
        # Attempt to refresh the access token
        access_token = refresh_access_token(request.session)
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(top_tracks_url, headers=headers, params=params)

    if response.status_code != 200:
        return JsonResponse(
            {"error": "Failed to retrieve top track.", "details": response.text},
            status=response.status_code
        )

    track_data = response.json()['items'][0]  # Get the first (top) track

    # Get track details
    track_name = track_data['name']
    artist_name = track_data['artists'][0]['name']
    duration_ms = track_data['duration_ms']

    # Convert to minutes and seconds for display
    minutes = duration_ms // (1000 * 60)
    seconds = (duration_ms % (1000 * 60)) // 1000

    return render(request, 'spotify_auth/listening_time.html', {
        "track_name": track_name,
        "artist_name": artist_name,
        "minutes": minutes,
        "seconds": seconds
    })


def spotify_wrap(request):
    top_tracks = get_top_tracks(request)
    top_artists = get_top_artists(request)
    top_genre = get_top_genre(request)
    new_artists_count = new_artists_discovered(request)
    personality_insights = get_personality_insights(request)

    context = {
        "top_tracks": top_tracks,
        "top_artists": top_artists,
        "top_genre": top_genre,
        "new_artists_count": new_artists_count,
        "personality_insights": personality_insights,
    }

    return render(request, 'spotify_auth/wrap.html', context)

def get_spotify_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}
