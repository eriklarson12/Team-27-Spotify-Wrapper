from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('spotify/', include('spotify_auth.urls')),  # Assuming your app is named spotify_auth
]