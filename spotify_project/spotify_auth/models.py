from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone  # For created_at field


class SpotifyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=255, unique=True)
    spotify_email = models.EmailField(unique=True)
    refresh_token = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username}'s Spotify Profile"


class SpotifyWrap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    top_tracks = models.JSONField()
    top_artists = models.JSONField()
    top_genre = models.CharField(max_length=255)
    genre_count = models.IntegerField(default=0)
    total_unique_genres = models.IntegerField(default=0)
    new_artists_count = models.IntegerField()
    personality_insights = models.TextField()

    # New field to track time range
    TIME_RANGE_CHOICES = [
        ('short_term', 'Short Term (Last 4 Weeks)'),
        ('medium_term', 'Medium Term (Last 6 Months)'),
        ('long_term', 'Long Term (All Time)')
    ]
    time_range = models.CharField(
        max_length=20,
        choices=TIME_RANGE_CHOICES,
        default='medium_term'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Spotify Wrap'
        verbose_name_plural = 'Spotify Wraps'

    def __str__(self):
        return f"{self.user.username}'s {self.get_time_range_display()} Wrap - {self.created_at.strftime('%Y-%m-%d')}"


