# Spotify Desktop Control

A PySide6 desktop Spotify controller with a C-60 cassette-style UI, RGB colour cycling, and a local FastAPI backend.

---

## Features

- Cassette player UI — animated reels, RGB-synced shell, album-art label strip
- Full playback control — play / pause / skip / seek / volume / shuffle / repeat
- Device switching — transfer playback between any active Spotify device
- Playlist browser — browse, play, add and remove tracks
- Search — find and queue tracks from Spotify's catalogue
- Library — Liked Songs and Recently Played tabs
- Like / unlike the current track with one click
- Non-blocking UI — async polling, album art fetched in background

---

## Project Structure

```
Spotify-Desktop-Control/
│
├── GUI/                            # PySide6 application
│   ├── app.py                      # Entry point — run this
│   ├── main_window.py              # SpotifyPlayerWindow (shell + controls)
│   ├── core/
│   │   ├── api_client.py           # HTTP client → FastAPI backend
│   │   ├── launcher.py             # Starts / health-checks the backend
│   │   ├── theme.py                # PALETTE + BASE_QSS stylesheet
│   │   └── utils.py                # Pure helpers (ms_to_mmss, detect_mood …)
│   ├── tabs/
│   │   ├── base_tab.py             # Shared BaseTab (status bar, queue helpers)
│   │   ├── queue_tab.py            # Up-next queue
│   │   ├── playlists_tab.py        # Playlist browser + track list
│   │   ├── search_tab.py           # Spotify search
│   │   └── library_tab.py          # Liked Songs + Recently Played
│   └── widgets/
│       └── cassette_widget.py      # C-60 cassette QPainter widget
│
├── backend/
│   ├── main.py                     # FastAPI routes
│   └── spotify_client.py           # Spotipy wrapper + retry logic
│
├── .env.example                    # Credentials template
├── requirements.txt
├── setup.bat                       # Windows one-click setup
├── run.bat                         # Windows one-click launch
├── .gitignore
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- A Spotify account
- A Spotify Developer App ([create one here](https://developer.spotify.com/dashboard))

### 1 — Clone the repo

```
git clone https://github.com/YOUR_USERNAME/Spotify-Desktop-Control.git
cd Spotify-Desktop-Control
```

### 2 — Create a virtual environment and install dependencies

**Windows (one click):**
```
setup.bat
```

**Manual:**
```
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate        # macOS / Linux
pip install -r requirements.txt
```

### 3 — Configure Spotify credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app.
2. Copy `Client ID` and `Client Secret`.
3. In the app settings add the Redirect URI: `http://localhost:8888/callback`
4. Copy the credentials file:

```
cp .env.example backend/.env
```

Then open `backend/.env` and fill in:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

---

## Running

**Windows (one click):**
```
run.bat
```

**Manual:**
```
.venv\Scripts\activate
python GUI\app.py
```

On first run a browser window opens asking you to log in to Spotify. After authorising, a token cache is saved locally and you won't be asked again.

---

## Git workflow

```
# check what changed
git status

# stage and commit
git add .
git commit -m "your message"

# push to GitHub
git push origin main
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Controls do nothing | Open Spotify on any device and start playback once |
| Login fails | Check `backend/.env` credentials and that the Redirect URI matches exactly |
| App won't start | Make sure the venv is activated and all deps installed |
| Port 8000 in use | Kill the other process or change the port in `launcher.py` and `api_client.py` |

---

## License

MIT
