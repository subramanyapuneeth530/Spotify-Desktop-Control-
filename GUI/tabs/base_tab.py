"""
GUI/tabs/base_tab.py
Abstract base class for every tab in the right panel.

Provides:
  - _status(msg, ms)   — write to the main window's status bar
  - _queue_uri(uri)    — add a track URI to the Spotify queue
  - _queue_and_skip()  — queue + immediately skip to that track
  - _set_window(win)   — called by the main window after construction

All tabs inherit BaseTab so they share these helpers without duplicating code.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtCore    import QTimer
from PySide6.QtWidgets import QWidget

from GUI.core import api_client
from GUI.core.api_client import BackendError

if TYPE_CHECKING:
    from GUI.main_window import SpotifyPlayerWindow   # avoid circular import


class BaseTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._window: "SpotifyPlayerWindow | None" = None

    def _set_window(self, win: "SpotifyPlayerWindow"):
        self._window = win

    # ── shared helpers ─────────────────────────────────────────────────────

    def _status(self, msg: str, ms: int = 3000):
        if self._window:
            self._window.show_status(msg, ms)

    def _queue_uri(self, uri: str):
        try:
            api_client.add_to_queue(uri)
            self._status("Added to queue ✓")
            QTimer.singleShot(400, self._reload_queue)
        except BackendError as e:
            self._status(f"Queue error: {e.detail}", 4000)

    def _queue_and_skip(self, uri: str):
        try:
            api_client.add_to_queue(uri)
            api_client.next_track()
            self._status("Playing ▶")
        except BackendError as e:
            self._status(f"Error: {e.detail}", 4000)
        QTimer.singleShot(600, self._refresh_playback)

    def _reload_queue(self):
        if self._window:
            self._window.queue_tab.load()

    def _refresh_playback(self):
        if self._window:
            self._window.fetch_playback()
