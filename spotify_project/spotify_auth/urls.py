from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.spotify_login, name='spotify_login'),
    path('logout/', views.logout, name='logout'),
    path('callback/', views.spotify_callback, name='spotify_callback'),
    path('profile/', views.profile, name='profile'),
    path('top-tracks/', views.get_top_tracks, name='get_top_tracks'),
    path('top-artists/', views.get_top_artists, name='get_top_artists'),
    path('top-genre/', views.get_top_genre, name='get_top_genre'),
    path('personality_insights/', views.get_personality_insights, name='get_personality_insights'),
    path('new-artists/', views.new_artists_discovered, name='new_artists_discovered'),
    path('listening-time/', views.get_listening_time, name='get_listening_time'),
    path('spotify_wrap/', views.spotify_wrap, name='spotify_wrap'),
    path('wrap/save/', views.save_wrap, name='save_wrap'),
    path('wraps/', views.view_saved_wraps, name='view_saved_wraps'),
    path('wrap/<int:wrap_id>/', views.view_wrap, name='view_wrap'),
    path('save-wrap/', views.save_wrap, name='save_wrap'),
    path('view-saved-wraps/', views.view_saved_wraps, name='view_saved_wraps'),
    path('view-wrap/<int:wrap_id>/', views.view_wrap, name='view_wrap'),
    path('spotify-wrap/', views.spotify_wrap, name='spotify_wrap'),
    path('save-wrap/', views.save_wrap, name='save_wrap'),
    path('delete_wrap/<int:wrap_id>/', views.delete_wrap, name='delete_wrap'),
]
