# admin.py

from django.contrib import admin
from .models import SpotifyProfile, SpotifyWrap


@admin.register(SpotifyProfile)
class SpotifyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'spotify_id', 'spotify_email')
    search_fields = ('user__username', 'spotify_id', 'spotify_email')
    list_filter = ('user__is_active',)

    def get_readonly_fields(self, request, obj=None):
        # Make fields readonly if the object already exists
        if obj:
            return ('spotify_id', 'spotify_email', 'refresh_token')
        return ()


@admin.register(SpotifyWrap)
class SpotifyWrapAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'top_genre', 'new_artists_count')
    list_filter = ('created_at', 'top_genre')
    search_fields = ('user__username', 'top_genre')
    readonly_fields = ('created_at',)

    def get_readonly_fields(self, request, obj=None):
        # Make all fields readonly if the object already exists
        if obj:
            return ('user', 'created_at', 'top_tracks', 'top_artists',
                    'top_genre', 'new_artists_count', 'personality_insights')
        return ('created_at',)