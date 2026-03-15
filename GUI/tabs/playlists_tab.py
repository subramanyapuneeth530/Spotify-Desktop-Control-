"""
GUI/tabs/playlists_tab.py
Browse playlists, view tracks, play / add / remove.
Needs a reference to the main window for current_track_uri and device_combo.
"""
import webbrowser

from PySide6.QtCore    import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton,
)

from GUI.tabs.base_tab   import BaseTab
from GUI.core            import api_client
from GUI.core.api_client import BackendError
from GUI.core.utils      import section_label, make_track_item


class PlaylistsTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # ── left: playlist list ──────────────────────────────────────────
        left = QVBoxLayout()
        left.addWidget(section_label("Playlists"))

        self.playlist_list = QListWidget()
        self.playlist_list.itemSelectionChanged.connect(self._on_playlist_selected)
        left.addWidget(self.playlist_list)

        pl_btns = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.open_btn = QPushButton("Open in Spotify")
        pl_btns.addWidget(self.play_btn)
        pl_btns.addWidget(self.open_btn)
        left.addLayout(pl_btns)

        self.add_track_btn = QPushButton("+ Add Current Track")
        left.addWidget(self.add_track_btn)

        self.play_btn.clicked.connect(self._on_play)
        self.open_btn.clicked.connect(self._on_open)
        self.add_track_btn.clicked.connect(self._on_add_current)

        # ── right: track list ────────────────────────────────────────────
        right = QVBoxLayout()
        right.addWidget(section_label("Tracks"))

        self.tracks_list = QListWidget()
        right.addWidget(self.tracks_list)

        tr_btns = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Selected")
        self.queue_btn  = QPushButton("+ Add to Queue")
        tr_btns.addWidget(self.remove_btn)
        tr_btns.addWidget(self.queue_btn)
        right.addLayout(tr_btns)

        self.remove_btn.clicked.connect(self._on_remove)
        self.queue_btn.clicked.connect(self._on_queue_track)

        layout.addLayout(left,  stretch=1)
        layout.addLayout(right, stretch=2)

        # state
        self._current_playlist_id:  str | None = None
        self._current_playlist_url: str | None = None

    # ── data loading ───────────────────────────────────────────────────────

    def load_playlists(self):
        try:
            data = api_client.get_playlists()
        except BackendError as e:
            self._status(f"Playlist error: {e.detail}", 4000); return

        self.playlist_list.clear()
        for pl in data.get("playlists", []):
            name  = pl.get("name", "Unnamed")
            total = pl.get("tracks_total") or 0
            item  = QListWidgetItem(f"{name}  ({total} tracks)")
            item.setData(Qt.UserRole,     pl.get("id"))
            item.setData(Qt.UserRole + 1, pl.get("external_url"))
            item.setToolTip(f"{name}\nOwner: {pl.get('owner', '')}")
            self.playlist_list.addItem(item)

    def _load_tracks(self, pid: str):
        try:
            data = api_client.get_playlist_tracks(pid)
        except BackendError as e:
            self._status(f"Track load error: {e.detail}", 4000); return

        self.tracks_list.clear()
        for tr in data.get("tracks", []):
            self.tracks_list.addItem(make_track_item(
                tr.get("name", ""), tr.get("artists", ""),
                tr.get("duration_ms", 0), tr.get("uri"), tr.get("id"),
                tr.get("explicit", False),
            ))

    # ── callbacks ──────────────────────────────────────────────────────────

    def _on_playlist_selected(self):
        items = self.playlist_list.selectedItems()
        if not items: return
        self._current_playlist_id  = items[0].data(Qt.UserRole)
        self._current_playlist_url = items[0].data(Qt.UserRole + 1)
        if self._current_playlist_id:
            self._load_tracks(self._current_playlist_id)

    def _on_play(self):
        if not self._current_playlist_id:
            self._status("Select a playlist first"); return
        did = self._window.device_combo.currentData() if self._window else None
        try:
            api_client.play_playlist(self._current_playlist_id, device_id=did)
            self._status("Playing playlist ▶")
        except BackendError as e:
            self._status(f"Error: {e.detail}", 4000)

    def _on_open(self):
        if self._current_playlist_url:
            webbrowser.open(self._current_playlist_url)

    def _on_add_current(self):
        if not self._current_playlist_id:
            self._status("Select a playlist first"); return
        uri = self._window.current_track_uri if self._window else None
        if not uri:
            self._status("No track currently playing"); return
        try:
            api_client.add_track_to_playlist(self._current_playlist_id, uri)
            self._status("Added current track to playlist ✓")
            self._load_tracks(self._current_playlist_id)
        except BackendError as e:
            self._status(f"Error: {e.detail}", 4000)

    def _on_remove(self):
        if not self._current_playlist_id:
            self._status("Select a playlist first"); return
        items = self.tracks_list.selectedItems()
        if not items:
            self._status("Select a track to remove"); return
        try:
            api_client.remove_track_from_playlist(
                self._current_playlist_id, items[0].data(Qt.UserRole))
            self._status("Track removed ✓")
            self._load_tracks(self._current_playlist_id)
        except BackendError as e:
            self._status(f"Error: {e.detail}", 4000)

    def _on_queue_track(self):
        items = self.tracks_list.selectedItems()
        if not items:
            self._status("Select a track first"); return
        uri = items[0].data(Qt.UserRole)
        if uri: self._queue_uri(uri)

    # ── property used by other tabs ────────────────────────────────────────
    @property
    def current_playlist_id(self) -> str | None:
        return self._current_playlist_id
