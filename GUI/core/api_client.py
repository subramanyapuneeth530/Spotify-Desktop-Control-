"""
GUI/core/api_client.py
HTTP client between the GUI and the FastAPI backend.
Every network call goes through _get() or _post() — one error type everywhere.
"""
import requests
from requests.exceptions import ConnectionError, Timeout

BASE_URL        = "http://127.0.0.1:8000"
_DEFAULT_TIMEOUT = 5
_SLOW_TIMEOUT    = 12


class BackendError(Exception):
    """Raised when the backend returns an HTTP error or is unreachable."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail      = detail
        super().__init__(f"[{status_code}] {detail}")


def _get(path: str, params: dict = None, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    try:
        r = requests.get(f"{BASE_URL}{path}", params=params, timeout=timeout)
        _check(r); return r.json()
    except (ConnectionError, Timeout):
        raise BackendError(0, "Cannot connect to backend. Is it running?")

def _post(path: str, payload: dict = None, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    try:
        r = requests.post(f"{BASE_URL}{path}", json=payload or {}, timeout=timeout)
        _check(r); return r.json()
    except (ConnectionError, Timeout):
        raise BackendError(0, "Cannot connect to backend. Is it running?")

def _check(r: requests.Response):
    if not r.ok:
        try:    detail = r.json().get("detail", r.text)
        except: detail = r.text
        raise BackendError(r.status_code, detail)


# ── playback ──────────────────────────────────────────────────────────────
def get_playback_state() -> dict:           return _get("/playback/state")
def play():                                 _post("/playback/play")
def pause():                                _post("/playback/pause")
def next_track():                           _post("/playback/next")
def previous_track():                       _post("/playback/previous")
def seek(position_ms: int):                 _post("/playback/seek", {"position_ms": int(position_ms)})
def set_volume(volume_percent: int):        _post("/playback/volume", {"volume_percent": int(volume_percent)})
def set_shuffle(state: bool):               _post("/playback/shuffle", {"state": bool(state)})
def set_repeat(mode: str):                  _post("/playback/repeat", {"mode": mode})

# ── devices ───────────────────────────────────────────────────────────────
def get_devices() -> dict:                  return _get("/devices")
def transfer_playback(device_id: str, force_play: bool = False):
    _post("/devices/transfer", {"device_id": device_id, "force_play": force_play})

# ── playlists ─────────────────────────────────────────────────────────────
def get_playlists(limit=50, offset=0) -> dict:
    return _get("/playlists", {"limit": limit, "offset": offset}, _SLOW_TIMEOUT)
def get_playlist_tracks(playlist_id: str, limit=100, offset=0) -> dict:
    return _get(f"/playlists/{playlist_id}/tracks", {"limit": limit, "offset": offset}, _SLOW_TIMEOUT)
def play_playlist(playlist_id: str, device_id: str = None):
    _post("/playlists/play", {"playlist_id": playlist_id, "device_id": device_id}, _SLOW_TIMEOUT)
def add_track_to_playlist(playlist_id: str, track_uri: str):
    _post(f"/playlists/{playlist_id}/add_track", {"track_uri": track_uri}, _SLOW_TIMEOUT)
def remove_track_from_playlist(playlist_id: str, track_uri: str):
    _post(f"/playlists/{playlist_id}/remove_track", {"track_uri": track_uri}, _SLOW_TIMEOUT)

# ── queue ─────────────────────────────────────────────────────────────────
def get_queue() -> dict:                    return _get("/queue")
def add_to_queue(track_uri: str):           _post("/queue/add", {"track_uri": track_uri})
def clear_queue():                          _post("/queue/clear")

# ── search ────────────────────────────────────────────────────────────────
def search(query: str, search_type: str = "track", limit: int = 20) -> dict:
    return _get("/search", {"q": query, "type": search_type, "limit": limit}, _SLOW_TIMEOUT)

# ── library ───────────────────────────────────────────────────────────────
def get_recently_played(limit: int = 20) -> dict:
    return _get("/recently-played", {"limit": limit})
def get_liked_songs(limit: int = 50, offset: int = 0) -> dict:
    return _get("/liked-songs", {"limit": limit, "offset": offset}, _SLOW_TIMEOUT)
def like_track(track_id: str):              _post("/liked-songs/add",    {"track_id": track_id})
def unlike_track(track_id: str):            _post("/liked-songs/remove", {"track_id": track_id})
def is_track_liked(track_id: str) -> bool:
    return _get(f"/liked-songs/contains/{track_id}").get("liked", False)

# ── health ────────────────────────────────────────────────────────────────
def health_check() -> bool:
    try:    return requests.get(f"{BASE_URL}/health", timeout=2).ok
    except: return False
