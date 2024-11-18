from collections import Counter

import requests
from django.conf import settings
from django.http import JsonResponse
import base64
import urllib.parse
from django.shortcuts import render, redirect

from urllib.parse import quote
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import SpotifyProfile
from django.contrib.auth import logout as auth_logout
from collections import Counter
import secrets
import string
import requests
from django.conf import settings
from django.http import JsonResponse
import base64
import urllib.parse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import SpotifyProfile
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required  # Add this import at the top
from collections import Counter
import requests
from django.conf import settings
from django.http import JsonResponse
import base64
import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import SpotifyProfile, SpotifyWrap  # Add SpotifyWrap to imports
from django.contrib.auth import logout as auth_logout

def index(request):
    """
    View for the home/landing page
    """
    return render(request, 'spotify_auth/index.html')

def home(request):
    """
    View for the home/landing page
    """
    return render(request, 'spotify_auth/home.html')

def spotify_login(request):
    # Spotify OAuth endpoint
    auth_url = "https://accounts.spotify.com/authorize"

    # Parameters for the OAuth URL
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": "user-read-private user-read-email user-top-read",  # Added user-top-read scope
        "show_dialog": "true"
    }
    # Redirect to Spotify's login page
    return redirect(f"{auth_url}?{urllib.parse.urlencode(params)}")


def logout(request):
    """
    Clear session data and redirect to home page
    """
    # Clear all session data
    request.session.flush()

    # Logout Django user
    auth_logout(request)

    # Invalidate any existing Spotify authorization by modifying the login URL
    request.session['force_login'] = True

    # Redirect to home page
    return redirect('home')





def spotify_callback(request):
    # Check for error parameter which Spotify sends when user denies access
    if request.GET.get('error'):
        return redirect('home')

    code = request.GET.get("code")
    if not code:
        return redirect('home')

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

        # Store tokens in session
        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token

        # Get user profile from Spotify
        spotify_user = get_spotify_user_data(access_token)

        if spotify_user:
            # Check if we already have a user with this Spotify ID
            try:
                spotify_profile = SpotifyProfile.objects.get(spotify_id=spotify_user['id'])
                user = spotify_profile.user
            except SpotifyProfile.DoesNotExist:
                # Create new user and profile
                username = f"spotify_{spotify_user['id']}"
                email = spotify_user.get('email', '')

                # Generate a secure random password
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for i in range(32))

                # Create Django user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password  # Using our secure random password
                )

                # Create Spotify profile
                spotify_profile = SpotifyProfile.objects.create(
                    user=user,
                    spotify_id=spotify_user['id'],
                    spotify_email=email,
                    refresh_token=refresh_token
                )

            # Log the user in
            login(request, user)
            return redirect('profile')

    return redirect('home')


def get_spotify_user_data(access_token):
    """Helper function to get user data from Spotify"""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code == 200:
        return response.json()
    return None

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

    # Add Django user data to context
    context = {
        "profile": profile_data,
        "django_user": request.user,
        "spotify_profile": request.user.spotifyprofile
    }

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
    return [(track["name"], track.get("preview_url", None)) for track in tracks]



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



def get_spotify_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}



@login_required
def view_saved_wraps(request):
    """View all saved wraps for the current user"""
    wraps = SpotifyWrap.objects.filter(user=request.user)
    return render(request, 'spotify_auth/saved_wraps.html', {'wraps': wraps})


@login_required
def view_wrap(request, wrap_id):
    """View a specific saved wrap"""
    wrap = get_object_or_404(SpotifyWrap, id=wrap_id, user=request.user)
    context = {
        'top_tracks': wrap.top_tracks,
        'top_artists': wrap.top_artists,
        'top_genre': wrap.top_genre,
        'new_artists_count': wrap.new_artists_count,
        'personality_insights': wrap.personality_insights,
        'created_at': wrap.created_at,
        'is_saved_wrap': True
    }
    return render(request, 'spotify_auth/wrap.html', context)


# views.py

@login_required
def spotify_wrap(request):
    """Generate and display a new Spotify wrap"""
    try:
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
            "is_saved_wrap": False
        }

        return render(request, 'spotify_auth/wrap.html', context)
    except Exception as e:
        print(f"Error generating wrap: {str(e)}")
        return redirect('profile')


@login_required
def save_wrap(request):
    """Save the current Spotify wrap data"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        # Get the data
        top_tracks = get_top_tracks(request)
        top_artists = get_top_artists(request)
        top_genre = get_top_genre(request)
        new_artists_count = new_artists_discovered(request)
        personality_insights = get_personality_insights(request)

        # Print debug information
        print(f"Saving wrap for user: {request.user.username}")
        print(f"Top tracks: {top_tracks}")
        print(f"Top artists: {top_artists}")
        print(f"Top genre: {top_genre}")
        print(f"New artists count: {new_artists_count}")

        # Create the wrap object
        wrap = SpotifyWrap.objects.create(
            user=request.user,
            top_tracks=top_tracks,
            top_artists=top_artists,
            top_genre=top_genre,
            new_artists_count=new_artists_count,
            personality_insights=personality_insights if isinstance(personality_insights, str) else str(
                personality_insights)
        )

        return JsonResponse({
            'status': 'success',
            'wrap_id': wrap.id,
            'message': 'Wrap saved successfully!'
        })
    except Exception as e:
        print(f"Error saving wrap: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error saving wrap: {str(e)}'
        }, status=500)


# In views.py
from django.contrib import messages
from django.http import JsonResponse

@login_required
def delete_wrap(request, wrap_id):
    """Delete a specific saved wrap"""
    try:
        # Find the wrap and ensure it belongs to the current user
        wrap = get_object_or_404(SpotifyWrap, id=wrap_id, user=request.user)

        # Delete the wrap
        wrap.delete()

        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Wrap deleted successfully!'
            })

        # For non-AJAX requests, add a message and redirect
        messages.success(request, 'Wrap deleted successfully!')
        return redirect('view_saved_wraps')

    except Exception as e:
        # Handle any errors
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': f'Error deleting wrap: {str(e)}'
            }, status=500)

        messages.error(request, f'Error deleting wrap: {str(e)}')
        return redirect('view_saved_wraps')