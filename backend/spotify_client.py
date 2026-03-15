"""
spotify_client.py
Spotipy OAuth wrapper with retry logic.
All direct Spotify API calls live here — nowhere else.
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("SPOTIFY_REDIRECT_URI")

SCOPES = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "playlist-read-private "
    "playlist-modify-private "
    "playlist-modify-public "
    "user-library-read "
    "user-top-read "
)

logger = logging.getLogger(__name__)

if not (CLIENT_ID and CLIENT_SECRET and REDIRECT_URI):
    raise RuntimeError(
        "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID, "
        "SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI in backend/.env"
    )


def _retry(fn, retries: int = 2, delay: float = 0.5):
    for attempt in range(retries + 1):
        try:
            return fn()
        except SpotifyException as e:
            if attempt == retries:
                raise
            logger.warning("Spotify API error (attempt %d/%d): %s", attempt + 1, retries, e)
            time.sleep(delay)


class SpotifyClient:
    def __init__(self):
        auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES,
            cache_path=str(BASE_DIR / ".spotify_token_cache"),
            show_dialog=False,
            open_browser=True,
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager,
                                   requests_timeout=10, retries=3)

    # ── playback ──────────────────────────────────────────────────────────
    def get_playback_state(self):           return _retry(lambda: self.sp.current_playback())
    def play(self, **kw):                   _retry(lambda: self.sp.start_playback(**kw))
    def pause(self):                        _retry(lambda: self.sp.pause_playback())
    def next(self):                         _retry(lambda: self.sp.next_track())
    def previous(self):                     _retry(lambda: self.sp.previous_track())
    def seek(self, ms: int):                _retry(lambda: self.sp.seek_track(max(0, int(ms))))
    def set_volume(self, v: int):           _retry(lambda: self.sp.volume(max(0, min(100, int(v)))))
    def set_shuffle(self, state: bool):     _retry(lambda: self.sp.shuffle(state))
    def set_repeat(self, mode: str):
        if mode not in ("off", "track", "context"): mode = "off"
        _retry(lambda: self.sp.repeat(mode))

    # ── devices ───────────────────────────────────────────────────────────
    def get_devices(self):                  return _retry(lambda: self.sp.devices()) or {}
    def transfer_playback(self, device_id: str, force_play: bool = False):
        _retry(lambda: self.sp.transfer_playback(device_id=device_id, force_play=force_play))

    # ── playlists ─────────────────────────────────────────────────────────
    def get_playlists(self, limit=50, offset=0):
        return _retry(lambda: self.sp.current_user_playlists(limit=limit, offset=offset)) or {}
    def get_playlist_tracks(self, pid: str, limit=100, offset=0):
        return _retry(lambda: self.sp.playlist_items(pid, limit=limit, offset=offset)) or {}
    def play_playlist(self, pid: str, device_id: Optional[str] = None):
        kw = {"context_uri": f"spotify:playlist:{pid}"}
        if device_id: kw["device_id"] = device_id
        _retry(lambda: self.sp.start_playback(**kw))
    def add_track_to_playlist(self, pid: str, uri: str):
        _retry(lambda: self.sp.playlist_add_items(pid, [uri]))
    def remove_track_from_playlist(self, pid: str, uri: str):
        _retry(lambda: self.sp.playlist_remove_all_occurrences_of_items(pid, [uri]))

    # ── queue ─────────────────────────────────────────────────────────────
    def get_queue(self):                    return _retry(lambda: self.sp.queue()) or {}
    def add_to_queue(self, uri: str):       _retry(lambda: self.sp.add_to_queue(uri))
    def clear_queue(self):
        raise RuntimeError("Clearing the queue is not supported by the Spotify Web API.")

    # ── search / library ──────────────────────────────────────────────────
    def search(self, q: str, type_: str = "track", limit: int = 20):
        if type_ not in ("track","album","artist","playlist"): type_ = "track"
        return _retry(lambda: self.sp.search(q=q, type=type_, limit=limit)) or {}
    def get_recently_played(self, limit=20):
        return _retry(lambda: self.sp.current_user_recently_played(limit=limit)) or {}
    def get_liked_songs(self, limit=50, offset=0):
        return _retry(lambda: self.sp.current_user_saved_tracks(limit=limit, offset=offset)) or {}
    def like_track(self, tid: str):         _retry(lambda: self.sp.current_user_saved_tracks_add([tid]))
    def unlike_track(self, tid: str):       _retry(lambda: self.sp.current_user_saved_tracks_delete([tid]))
    def is_track_liked(self, tid: str) -> bool:
        r = _retry(lambda: self.sp.current_user_saved_tracks_contains([tid]))
        return bool(r and r[0])
