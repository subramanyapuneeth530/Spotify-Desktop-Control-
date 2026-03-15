"""
backend/main.py
FastAPI application — HTTP routes only.
Business logic lives in spotify_client.py.
"""
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from spotify_client import SpotifyClient

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Spotify Desktop Control", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

sp = SpotifyClient()


# ── helpers ───────────────────────────────────────────────────────────────

def _err(e: Exception) -> HTTPException:
    logger.error("Spotify error: %s", e)
    return HTTPException(status_code=500, detail=str(e))


# ── request models ────────────────────────────────────────────────────────

class SeekRequest(BaseModel):           position_ms: int = Field(ge=0)
class VolumeRequest(BaseModel):         volume_percent: int = Field(ge=0, le=100)
class ShuffleRequest(BaseModel):        state: bool
class RepeatRequest(BaseModel):         mode: str
class DeviceTransferRequest(BaseModel): device_id: str; force_play: bool = False
class PlaylistPlayRequest(BaseModel):   playlist_id: str; device_id: Optional[str] = None
class TrackModifyRequest(BaseModel):    track_uri: str
class QueueAddRequest(BaseModel):       track_uri: str
class LikeRequest(BaseModel):           track_id: str


# ── playback ──────────────────────────────────────────────────────────────

@app.get("/playback/state")
def get_playback_state():
    try:    return sp.get_playback_state() or {}
    except Exception as e: raise _err(e)

@app.post("/playback/play")
def play():
    try:    sp.play(); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/playback/pause")
def pause():
    try:    sp.pause(); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/playback/next")
def next_track():
    try:    sp.next(); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/playback/previous")
def previous_track():
    try:    sp.previous(); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/playback/seek")
def seek(req: SeekRequest):
    try:    sp.seek(req.position_ms); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/playback/volume")
def set_volume(req: VolumeRequest):
    try:    sp.set_volume(req.volume_percent); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/playback/shuffle")
def set_shuffle(req: ShuffleRequest):
    try:    sp.set_shuffle(req.state); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/playback/repeat")
def set_repeat(req: RepeatRequest):
    try:    sp.set_repeat(req.mode); return {"status": "ok"}
    except Exception as e: raise _err(e)


# ── devices ───────────────────────────────────────────────────────────────

@app.get("/devices")
def get_devices():
    try:
        raw = sp.get_devices()
        return {"devices": [
            {"id": d.get("id"), "name": d.get("name"), "type": d.get("type"),
             "is_active": d.get("is_active"), "volume_percent": d.get("volume_percent")}
            for d in (raw.get("devices") or []) if d
        ]}
    except Exception as e: raise _err(e)

@app.post("/devices/transfer")
def transfer_playback(req: DeviceTransferRequest):
    try:    sp.transfer_playback(req.device_id, req.force_play); return {"status": "ok"}
    except Exception as e: raise _err(e)


# ── playlists ─────────────────────────────────────────────────────────────

@app.get("/playlists")
def get_playlists(limit: int = Query(50, ge=1, le=50), offset: int = Query(0, ge=0)):
    try:
        data = sp.get_playlists(limit=limit, offset=offset)
        return {"playlists": [
            {"id": pl.get("id"), "name": pl.get("name"),
             "tracks_total": (pl.get("tracks") or {}).get("total"),
             "external_url": (pl.get("external_urls") or {}).get("spotify"),
             "image_url": (((pl.get("images") or []) + [{}])[0]).get("url"),
             "owner": (pl.get("owner") or {}).get("display_name")}
            for pl in (data.get("items") or []) if pl
        ], "total": data.get("total", 0)}
    except Exception as e: raise _err(e)

@app.get("/playlists/{playlist_id}/tracks")
def get_playlist_tracks(playlist_id: str,
                        limit: int = Query(100, ge=1, le=100),
                        offset: int = Query(0, ge=0)):
    try:
        data  = sp.get_playlist_tracks(playlist_id, limit=limit, offset=offset)
        tracks = []
        for it in (data.get("items") or []):
            tr = (it or {}).get("track")
            if not tr or tr.get("is_local"): continue
            artists = ", ".join(a.get("name","") for a in (tr.get("artists") or []))
            album   = tr.get("album") or {}
            images  = album.get("images") or []
            tracks.append({
                "id": tr.get("id"), "name": tr.get("name"), "artists": artists,
                "uri": tr.get("uri"), "duration_ms": tr.get("duration_ms"),
                "album": album.get("name"), "image_url": images[0].get("url") if images else None,
                "added_at": it.get("added_at"), "explicit": tr.get("explicit", False),
            })
        return {"tracks": tracks, "total": data.get("total", 0)}
    except Exception as e: raise _err(e)

@app.post("/playlists/play")
def play_playlist(req: PlaylistPlayRequest):
    try:    sp.play_playlist(req.playlist_id, req.device_id); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/playlists/{playlist_id}/add_track")
def add_track_to_playlist(playlist_id: str, req: TrackModifyRequest):
    try:    sp.add_track_to_playlist(playlist_id, req.track_uri); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/playlists/{playlist_id}/remove_track")
def remove_track_from_playlist(playlist_id: str, req: TrackModifyRequest):
    try:    sp.remove_track_from_playlist(playlist_id, req.track_uri); return {"status": "ok"}
    except Exception as e: raise _err(e)


# ── queue ─────────────────────────────────────────────────────────────────

@app.get("/queue")
def get_queue():
    try:
        data = sp.get_queue()
        def _fmt(tr):
            if not tr: return None
            artists = ", ".join(a.get("name","") for a in (tr.get("artists") or []))
            images  = (tr.get("album") or {}).get("images") or []
            return {"id": tr.get("id"), "name": tr.get("name"), "artists": artists,
                    "uri": tr.get("uri"), "duration_ms": tr.get("duration_ms"),
                    "image_url": images[0].get("url") if images else None}
        return {"currently_playing": _fmt(data.get("currently_playing")),
                "queue": [t for t in (_fmt(tr) for tr in (data.get("queue") or [])) if t]}
    except Exception as e: raise _err(e)

@app.post("/queue/add")
def add_to_queue(req: QueueAddRequest):
    try:    sp.add_to_queue(req.track_uri); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/queue/clear")
def clear_queue():
    raise HTTPException(status_code=400,
        detail="Clearing the queue is not supported by the Spotify Web API.")


# ── search ────────────────────────────────────────────────────────────────

@app.get("/search")
def search(q: str = Query(..., min_length=1),
           type: str = Query("track"),
           limit: int = Query(20, ge=1, le=50)):
    try:
        data = sp.search(q, type_=type, limit=limit)
        tracks = []
        for tr in ((data.get("tracks") or {}).get("items") or []):
            if not tr: continue
            artists = ", ".join(a.get("name","") for a in (tr.get("artists") or []))
            images  = (tr.get("album") or {}).get("images") or []
            tracks.append({
                "id": tr.get("id"), "name": tr.get("name"), "artists": artists,
                "album": (tr.get("album") or {}).get("name"), "uri": tr.get("uri"),
                "duration_ms": tr.get("duration_ms"), "explicit": tr.get("explicit", False),
                "image_url": images[0].get("url") if images else None,
            })
        return {"tracks": tracks}
    except Exception as e: raise _err(e)


# ── library ───────────────────────────────────────────────────────────────

@app.get("/recently-played")
def recently_played(limit: int = Query(20, ge=1, le=50)):
    try:
        data = sp.get_recently_played(limit=limit)
        return {"tracks": [
            {"id": (it.get("track") or {}).get("id"),
             "name": (it.get("track") or {}).get("name"),
             "artists": ", ".join(a.get("name","") for a in ((it.get("track") or {}).get("artists") or [])),
             "uri": (it.get("track") or {}).get("uri"),
             "played_at": it.get("played_at"),
             "image_url": ((((it.get("track") or {}).get("album") or {}).get("images") or [{}])[0]).get("url")}
            for it in (data.get("items") or []) if it
        ]}
    except Exception as e: raise _err(e)

@app.get("/liked-songs")
def liked_songs(limit: int = Query(50, ge=1, le=50), offset: int = Query(0, ge=0)):
    try:
        data = sp.get_liked_songs(limit=limit, offset=offset)
        return {"tracks": [
            {"id": (it.get("track") or {}).get("id"),
             "name": (it.get("track") or {}).get("name"),
             "artists": ", ".join(a.get("name","") for a in ((it.get("track") or {}).get("artists") or [])),
             "uri": (it.get("track") or {}).get("uri"),
             "added_at": it.get("added_at"),
             "image_url": ((((it.get("track") or {}).get("album") or {}).get("images") or [{}])[0]).get("url")}
            for it in (data.get("items") or []) if it
        ], "total": data.get("total", 0)}
    except Exception as e: raise _err(e)

@app.post("/liked-songs/add")
def like_track(req: LikeRequest):
    try:    sp.like_track(req.track_id); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.post("/liked-songs/remove")
def unlike_track(req: LikeRequest):
    try:    sp.unlike_track(req.track_id); return {"status": "ok"}
    except Exception as e: raise _err(e)

@app.get("/liked-songs/contains/{track_id}")
def is_liked(track_id: str):
    try:    return {"liked": sp.is_track_liked(track_id)}
    except Exception as e: raise _err(e)


# ── health ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
