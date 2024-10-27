import requests
from django.shortcuts import redirect
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


def get_top_tracks(request):
    access_token = request.session.get('access_token')

    if not access_token:
        return redirect('spotify_login')

    top_tracks_url = "https://api.spotify.com/v1/me/top/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Parameters for the API request
    params = {
        "limit": 20,  # Number of tracks to retrieve
        "time_range": "medium_term"  # Options: long_term, medium_term, short_term
    }

    # Fetch top tracks data
    response = requests.get(top_tracks_url, headers=headers, params=params)

    if response.status_code == 403:
        # Attempt to refresh the access token
        access_token = refresh_access_token(request.session)
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(top_tracks_url, headers=headers, params=params)

    if response.status_code != 200:
        return JsonResponse(
            {"error": "Failed to retrieve top tracks.", "details": response.text},
            status=response.status_code
        )

    tracks_data = response.json()
    return render(request, 'spotify_auth/top_tracks.html', {"tracks": tracks_data['items']})

def get_top_artists(request):
    access_token = request.session.get('access_token')

    if not access_token:
        return redirect('spotify_login')

    top_artists_url = "https://api.spotify.com/v1/me/top/artists"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Parameters for the API request
    params = {
        "limit": 20,  # Number of artists to retrieve
        "time_range": "medium_term"  # Options: long_term, medium_term, short_term
    }

    # Fetch top artists data
    response = requests.get(top_artists_url, headers=headers, params=params)

    if response.status_code == 403:
        # Attempt to refresh the access token
        access_token = refresh_access_token(request.session)
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(top_artists_url, headers=headers, params=params)

    if response.status_code != 200:
        return JsonResponse(
            {"error": "Failed to retrieve top artists.", "details": response.text},
            status=response.status_code
        )

    artists_data = response.json()
    return render(request, 'spotify_auth/top_artists.html', {"artists": artists_data['items']})
