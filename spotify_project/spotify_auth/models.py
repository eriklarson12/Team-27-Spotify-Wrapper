from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class SpotifyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    spotify_id = models.CharField(max_length=255, unique=True)
    spotify_email = models.EmailField(unique=True)
    refresh_token = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username}'s Spotify Profile"