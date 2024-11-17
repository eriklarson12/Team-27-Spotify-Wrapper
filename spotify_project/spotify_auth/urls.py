from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.spotify_login, name='spotify_login'),
    path('callback/', views.spotify_callback, name='spotify_callback'),
    path('profile/', views.profile, name='profile'),
    path('top-tracks/', views.get_top_tracks, name='get_top_tracks'),
    path('top-artists/', views.get_top_artists, name='get_top_artists'),
    path('top-genre/', views.get_top_genre, name='get_top_genre'),
    path('personality_insights/', views.get_personality_insights, name='get_personality_insights'),
    path('new-artists/', views.new_artists_discovered, name='new_artists_discovered'),
    path('listening-time/', views.get_listening_time, name='get_listening_time'),
    path('spotify_wrap/', views.spotify_wrap, name='spotify_wrap'),
]
