<div align="center">

# Spotify Wrapper

Log in with Spotify and generate a shareable summary of your listening habits, with AI written personality insights and a trivia game built from your own library.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1.15-092E20?logo=django&logoColor=white)
![Spotify](https://img.shields.io/badge/Spotify-Web%20API-1DB954?logo=spotify&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-local-003B57?logo=sqlite&logoColor=white)

**[Team portfolio, demo video, and process writeup](https://foodfinderteamportfolio.godaddysites.com/)**

</div>

---

Spotify Wrapper is a Django web application that rebuilds the Spotify Wrapped experience on demand. You authorize the app through Spotify OAuth, pick a time range, and it pulls your top tracks, top artists, and dominant genre from the Spotify Web API, then presents them as a slideshow you can save or share.

Two features go past the official version. Google Gemini turns your top genres and artists into a written personality profile, and a generated trivia game quizzes you on your own listening history. Wraps are saved per user, so you can revisit a summary after your listening habits move on.

<!-- Screenshot: add a wrap slideshow capture to assets/ and reference it here with alt text. -->

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Team and Process](#team-and-process)
- [Limitations](#limitations)

## Features

- **Spotify OAuth login:** authorization code flow requesting `user-read-private`, `user-read-email`, and `user-top-read`, retrying with a refreshed access token when Spotify rejects a request.
- **Three time ranges:** the last four weeks, the last six months, or all time, selectable on any wrap.
- **Listening summary:** top ten tracks, top five artists, dominant genre with its artist count, total unique genres, and a count of artists new to the selected range.
- **AI personality insights:** Gemini reads your top five genres and artists and writes a description of your likely style, hobbies, and weekend, in roughly 150 to 200 words.
- **Music trivia:** three generated questions covering artist matching, genre counts, and unique artists, scored with per question feedback and a one hour session expiry.
- **Saved wraps:** store a wrap against your account, reopen it later, or delete it; share any wrap to X or LinkedIn through a prefilled post.
- **Account control:** a delete account action removes the user and cascades to the stored Spotify profile and every saved wrap.

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Django 5.1.15 (Python 3.12 or newer) |
| Data | SQLite, created locally on first migrate |
| Music data | Spotify Web API, authorization code OAuth flow |
| AI | Google Gemini through `google-generativeai` |
| Templates | Django templates with hand written CSS, no frontend framework |
| Auth | Django `contrib.auth`, with accounts provisioned from Spotify profiles |

## Getting Started

### Prerequisites

- Python 3.12 or newer
- A Spotify app from the [developer dashboard](https://developer.spotify.com/dashboard), for the client ID and secret
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

Register `http://127.0.0.1:8000/spotify/callback/` as a redirect URI on the Spotify app. Spotify rejects the login if it does not match exactly.

### Installation

```bash
git clone https://github.com/eriklarson12/Team-27-Spotify-Wrapper.git
cd Team-27-Spotify-Wrapper/spotify_project
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` before the first run. Generate a secret key with:

```bash
.venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Usage

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open http://127.0.0.1:8000 and choose to log in with Spotify. Spotify only serves listening data to accounts listed on the app, so add yourself as a user in the developer dashboard first. The database starts empty; a profile is created on your first successful login.

## Configuration

All configuration comes from the environment, loaded from `spotify_project/.env` at startup. See `.env.example`. Missing required values raise `ImproperlyConfigured` at startup rather than failing silently.

| Variable | Required | Purpose |
|---|---|---|
| `SECRET_KEY` | yes | Django cryptographic signing |
| `SPOTIFY_CLIENT_ID` | yes | Spotify app identifier |
| `SPOTIFY_CLIENT_SECRET` | yes | Spotify token exchange |
| `GOOGLE_GEMINI_API_KEY` | yes | personality insights generation |
| `SPOTIFY_REDIRECT_URI` | no | defaults to the local callback; must match the dashboard |
| `DEBUG` | no | defaults to `False`; set `True` only locally |
| `ALLOWED_HOSTS` | no | comma separated; required once `DEBUG` is off |

## Team and Process

Built by a team of five for Georgia Tech CS 2340. Full writeup, demo video, and individual profiles are on the [team portfolio site](https://foodfinderteamportfolio.godaddysites.com/).

| Name | Contribution |
|---|---|
| Marcos San Miguel | most of the backend, plus part of the front end |
| Erik Larson | backend functionality, data flow, and core logic |
| Aneegha Thithiesha Mahabaduge | backend features and front end contributions |
| Samuel Hauck | genre algorithm and the music trivia game |
| Cooper Brambley | majority of the front end, including CSS animations |

The team ran sprints against written planning documents, met twice weekly for scrum, tracked tasks on a Trello board, and paired on the harder integration work. Feature branches merged through GitHub.

## Limitations

- **Every wrap calls the Spotify API fresh.** Generating one summary makes eight requests, four of them just to count new artists across time ranges, with no caching or rate limiting.
- **Spotify development mode caps the audience.** Until the app passes Spotify's quota extension review, only accounts explicitly added in the developer dashboard can log in at all.
- **SQLite and `runserver` only.** The project was built and graded as a local development app, so there is no production database, WSGI server, or deployment configuration.
- **Test coverage is empty.** `tests.py` is a stub. The team relied on manual testing and code review during sprints.
- **Insights degrade silently.** If the Gemini call fails, the wrap still renders and the personality section falls back to a generic message rather than surfacing the error.
