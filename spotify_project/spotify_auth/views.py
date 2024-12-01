from collections import Counter

import requests, random, time
from django.contrib import messages
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

def team(request):
    return render(request, 'spotify_auth/team.html')

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


@login_required
def delete_account(request):
    """Delete user account and all associated data"""
    if request.method == 'POST':
        try:
            # Get the user
            user = request.user

            # Log the user out
            auth_logout(request)

            # Delete the user (this will cascade delete the SpotifyProfile due to the foreign key relationship)
            user.delete()

            # Redirect to home page with success message
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('home')

        except Exception as e:
            messages.error(request, f'Error deleting account: {str(e)}')
            return redirect('profile')

    # If not POST, redirect to profile
    return redirect('profile')


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


def get_top_tracks(request, time_range='medium_term'):
    access_token = request.session.get('access_token')
    if not access_token:
        return []

    url = "https://api.spotify.com/v1/me/top/tracks"
    headers = get_spotify_headers(access_token)
    params = {"limit": 10, "time_range": time_range}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return []

    tracks = response.json().get("items", [])
    return [(track["name"], track.get("preview_url", None), track["album"]["images"][0]["url"] if track["album"]["images"] else None) for track in tracks]

def get_top_artists(request, time_range='medium_term'):
    access_token = request.session.get('access_token')
    if not access_token:
        return []

    url = "https://api.spotify.com/v1/me/top/artists"
    headers = get_spotify_headers(access_token)
    params = {"limit": 5, "time_range": time_range}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return []

    artists = response.json().get("items", [])
    return [artist["name"] for artist in artists]

def get_top_genre(request, time_range='medium_term'):
    access_token = request.session.get('access_token')
    if not access_token:
        return "Unknown"

    url = "https://api.spotify.com/v1/me/top/artists"
    headers = get_spotify_headers(access_token)
    params = {"limit": 10, "time_range": time_range}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return "Unknown"

    artists = response.json().get("items", [])
    genres = [genre for artist in artists for genre in artist.get("genres", [])]
    top_genre = Counter(genres).most_common(1)
    return {
        "top_genre": top_genre[0][0] if top_genre else "Unknown",
        "genre_count": top_genre[0][1] if top_genre else 0,
        "total_unique_genres": len(set(genres))
    }

def get_personality_insights(request, t_r='medium_term'):
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
            "time_range": t_r
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
def new_artists_discovered(request, time_range='medium_term'):
    access_token = request.session.get('access_token')
    if not access_token:
        return 0

    url = "https://api.spotify.com/v1/me/top/artists"
    headers = get_spotify_headers(access_token)

    # Get artists for the selected time range
    selected_term_response = requests.get(url, headers=headers, params={"time_range": time_range})

    # Get artists for the long-term range for comparison
    long_term_response = requests.get(url, headers=headers, params={"time_range": "long_term"})

    medium_term_response = requests.get(url, headers=headers, params={"time_range": "medium_term"})

    short_term_response = requests.get(url, headers=headers, params={"time_range": "short_term"})

    if selected_term_response.status_code != 200 or long_term_response.status_code != 200:
        return 0

    selected_term_artists = {artist["name"] for artist in selected_term_response.json().get("items", [])}
    long_term_artists = {artist["name"] for artist in long_term_response.json().get("items", [])}
    medium_term_artists = {artist["name"] for artist in medium_term_response.json().get("items", [])}
    short_term_artists = {artist["name"] for artist in short_term_response.json().get("items", [])}
    # New artists are those in selected term data but not in long-term data
    if time_range == "long_term":
        return len(long_term_artists)
    if time_range == "medium_term":
        new_artists = medium_term_artists - long_term_artists
    else:
        new_artists = short_term_artists - medium_term_artists
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


def get_share_urls(request, wrap_data):
    """Generate sharing URLs for various social media platforms"""

    # Create base message for sharing
    base_message = f"Check out my Spotify Wrapped!\n\n" \
                   f"🎵 Top Genre: {wrap_data['top_genre']}\n" \
                   f"🎸 Top Artist: {wrap_data['top_artists'][0] if wrap_data['top_artists'] else 'N/A'}\n" \
                   f"🎼 New Artists Discovered: {wrap_data['new_artists_count']}\n" \
                   f"#SpotifyWrapped"

    # Get the full URL to the wrap
    wrap_url = request.build_absolute_uri()

    # Generate platform-specific URLs
    twitter_text = urllib.parse.quote(base_message)
    twitter_url = f"https://twitter.com/intent/tweet?text={twitter_text}&url={urllib.parse.quote(wrap_url)}"

    linkedin_text = urllib.parse.quote(base_message)
    linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(wrap_url)}&summary={linkedin_text}"

    return {
        'twitter_url': twitter_url,
        'linkedin_url': linkedin_url,
    }


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
        'genre_count': wrap.genre_count,
        'total_unique_genres': wrap.total_unique_genres,
        'new_artists_count': wrap.new_artists_count,
        'personality_insights': wrap.personality_insights,
        'created_at': wrap.created_at,
        'is_saved_wrap': True
    }

    # Generate sharing URLs
    share_urls = get_share_urls(request, context)
    context.update(share_urls)

    return render(request, 'spotify_auth/wrap.html', context)


# views.py

def spotify_wrap(request):
    """Generate and display a new Spotify wrap"""
    # Add time range selection, default to medium_term
    time_range = request.GET.get('time_range', request.session.get('selected_time_range', 'medium_term'))

    request.session['selected_time_range'] = time_range

    try:
        top_tracks = get_top_tracks(request, time_range)
        top_artists = get_top_artists(request, time_range)
        genre_data = get_top_genre(request, time_range)
        top_genre = genre_data['top_genre']
        genre_count = genre_data['genre_count']
        total_unique_genres = genre_data['total_unique_genres']
        new_artists_count = new_artists_discovered(request, time_range)
        personality_insights = get_personality_insights(
            request, time_range)  # Note: You might want to modify this to use time_range

        context = {
            "top_tracks": top_tracks,
            "top_artists": top_artists,
            "top_genre": top_genre,
            "genre_count": genre_count,
            "total_unique_genres": total_unique_genres,
            "new_artists_count": new_artists_count,
            "personality_insights": personality_insights,
            "is_saved_wrap": False,
            "selected_time_range": time_range,
            # "time_range": time_range  # Pass selected time range to template
        }

        # Generate sharing URLs
        share_urls = get_share_urls(request, context)
        context.update(share_urls)

        return render(request, 'spotify_auth/wrap.html', context)
    except Exception as e:
        print(f"Error generating wrap: {str(e)}")
        return redirect('profile')



@login_required
def save_wrap(request):
    """Save the current Spotify wrap data"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    # Get the time range from the POST data, with 'medium_term' as fallback
    time_range = request.POST.get('time_range', 'medium_term')

    try:
        # Get the data using the PASSED time range, not a hardcoded default
        top_tracks = get_top_tracks(request, time_range)
        top_artists = get_top_artists(request, time_range)
        genre_data = get_top_genre(request, time_range)
        top_genre = genre_data['top_genre']
        genre_count = genre_data['genre_count']
        total_unique_genres = genre_data['total_unique_genres']
        new_artists_count = new_artists_discovered(request, time_range)
        personality_insights = get_personality_insights(request, time_range)

        # Create the wrap object with the PASSED time range
        wrap = SpotifyWrap.objects.create(
            user=request.user,
            top_tracks=top_tracks,
            top_artists=top_artists,
            top_genre=top_genre,
            genre_count=genre_count,
            total_unique_genres=total_unique_genres,
            new_artists_count=new_artists_count,
            personality_insights=personality_insights if isinstance(personality_insights, str) else str(
                personality_insights),
            time_range=time_range  # Use the time range passed from frontend
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

def get_top_tracks_and_artist(request, time_range='medium_term'):
    access_token = request.session.get('access_token')
    if not access_token:
        return []

    url = "https://api.spotify.com/v1/me/top/tracks"
    headers = get_spotify_headers(access_token)
    params = {"limit": 5, "time_range": time_range}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return []

    tracks = response.json().get("items", [])
    return [(track["name"], track.get("preview_url", None), track["artists"][0]["name"]) for track in tracks]

@login_required
def create_music_trivia_game(request):
    """Generate a music trivia game based on the user's top tracks and artists"""

    time_range = request.session.get('selected_time_range',
                                     request.GET.get('time_range', 'medium_term'))
    request.session['time_range'] = time_range


    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('spotify_login')

    # Get top tracks and artists
    top_tracks = get_top_tracks_and_artist(request, time_range)
    top_artists = get_top_artists(request, time_range)

    # Generate trivia questions
    trivia_questions = []

    # Artist Matching Question
    if top_tracks and top_artists:
        track_num = random.randint(0, len(top_tracks) - 1)
        artist_match_question = {
            'type': 'artist_match',
            'question': 'Which of these artists performs the following track?',
            'track': top_tracks[track_num][0],
            'correct_answer': top_tracks[track_num][2],
            'options': random.sample(top_artists[0:3] + [top_tracks[track_num][2]], 4)
        }
        trivia_questions.append(artist_match_question)

    # Genre Knowledge Question
    genre_info = get_top_genre(request, time_range)
    genre_count = genre_info['genre_count']
    num_list1 = set([genre_count])
    while len(num_list1) < 4:
        incorrect_answer = random.randint(max(0, genre_count - 2), genre_count + 5)
        num_list1.add(incorrect_answer)
    num_list1 = list(num_list1)
    random.shuffle(num_list1)
    if genre_info:
        genre_question = {
            'type': 'genre_knowledge',
            'question': f'How many of your top artists belong to the {genre_info["top_genre"]} genre?',
            'correct_answer': genre_count,
            'options': num_list1
        }
        trivia_questions.append(genre_question)

    # Unique Artists Question
    unique = len(set([track[0] for track in top_tracks]))
    num_list2 = set([unique])
    while len(num_list2) < 4:
        incorrect_answer = random.randint(max(0, unique - 2), unique + 5)
        num_list2.add(incorrect_answer)
    num_list2 = list(num_list2)
    random.shuffle(num_list2)
    unique_artists_question = {
        'type': 'unique_artists',
        'question': 'How many unique artists appear in your top tracks?',
        'correct_answer': unique,
        'options': num_list2
    }
    trivia_questions.append(unique_artists_question)

    # Shuffle questions to randomize order
    random.shuffle(trivia_questions)

    request.session['trivia_questions'] = trivia_questions
    request.session['trivia_timestamp'] = int(time.time())
    request.session.set_expiry(3600)

    context = {
        'trivia_questions': trivia_questions,
        'top_tracks': top_tracks,
        'top_artists': top_artists,
        'time_range': time_range
    }

    return render(request, 'spotify_auth/music_trivia_game.html', context)


@login_required
def submit_music_trivia(request):
    """
    Process trivia game submission and calculate score
    """
    time_range = request.GET.get('time_range', 'medium_term')

    if request.method != 'POST':
        return redirect('create_music_trivia_game')

        # Retrieve questions from session
    trivia_questions = request.session.get('trivia_questions', [])

    # Check if questions exist and haven't expired
    if not trivia_questions:
        messages.error(request, 'Trivia session has expired. Please start a new game.')
        return redirect('create_music_trivia_game')

    # Validate session timestamp to prevent replay attacks
    session_timestamp = request.session.get('trivia_timestamp', 0)
    current_time = int(time.time())
    if current_time - session_timestamp > 3600:  # 1-hour expiration
        messages.error(request, 'Trivia session has expired. Please start a new game.')
        return redirect('create_music_trivia_game')

    user_answers = [request.POST.get('user_answer_0'), request.POST.get('user_answer_1'), request.POST.get('user_answer_2')]

    # Validate number of answers matches number of questions
    if len(user_answers) != len(trivia_questions):
        messages.error(request, 'Invalid submission. Please answer all questions.')
        return redirect('create_music_trivia_game')

    score = 0
    total_questions = len(trivia_questions)
    detailed_results = []

    for i, question in enumerate(trivia_questions):
        # Cast to string to ensure type consistency
        user_answer = str(user_answers[i])
        correct_answer = str(question['correct_answer'])

        # Track detailed results for feedback
        result = {
            'question': question['question'],
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': user_answer == correct_answer
        }

        if user_answer == correct_answer:
            score += 1

        detailed_results.append(result)

    # Clear the session to prevent replay
    del request.session['trivia_questions']
    del request.session['trivia_timestamp']

    # Prepare context for results template
    context = {
        'score': score,
        'total_questions': total_questions,
        'percentage': (score / total_questions) * 100 if total_questions > 0 else 0,
        'detailed_results': detailed_results,
        'time_range': time_range
    }

    return render(request, 'spotify_auth/music_trivia_results.html', context)