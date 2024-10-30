from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.spotify_login, name='spotify_login'),
    path('callback/', views.spotify_callback, name='spotify_callback'),
    path('profile/', views.profile, name='profile'),
    path('top-tracks/', views.get_top_tracks, name='get_top_tracks'),
    path('top-artists/', views.get_top_artists, name='get_top_artists'),
    path('top-genre/', views.get_top_genre, name='get_top_genre')
]