from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.spotify_login, name='spotify_login'),
    path('team/', views.team, name='team'),
    path('logout/', views.logout, name='logout'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('callback/', views.spotify_callback, name='spotify_callback'),
    path('profile/', views.profile, name='profile'),
    path('listening-time/', views.get_listening_time, name='get_listening_time'),
    path('spotify-wrap/', views.spotify_wrap, name='spotify_wrap'),
    path('save-wrap/', views.save_wrap, name='save_wrap'),
    path('view-saved-wraps/', views.view_saved_wraps, name='view_saved_wraps'),
    path('view-wrap/<int:wrap_id>/', views.view_wrap, name='view_wrap'),
    # Path keeps the underscore form: saved_wraps.html builds this URL in JavaScript.
    path('delete_wrap/<int:wrap_id>/', views.delete_wrap, name='delete_wrap'),
    path('music-trivia/', views.create_music_trivia_game, name='create_music_trivia_game'),
    path('music-trivia/submit/', views.submit_music_trivia, name='submit_music_trivia'),
]
