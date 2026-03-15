"""
GUI/tabs/search_tab.py
Spotify track search with Play / Queue / Add-to-Playlist actions.
"""
from PySide6.QtCore    import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QPushButton

from GUI.tabs.base_tab   import BaseTab
from GUI.core            import api_client
from GUI.core.api_client import BackendError
from GUI.core.utils      import accent_btn, make_track_item


class SearchTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # search bar
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs, artists, albums…")
        self.search_input.returnPressed.connect(self.do_search)
        self.search_go_btn = accent_btn("Search")
        self.search_go_btn.clicked.connect(self.do_search)
        search_row.addWidget(self.search_input)
        search_row.addWidget(self.search_go_btn)
        layout.addLayout(search_row)

        # results list
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_play)
        layout.addWidget(self.results_list)

        # action buttons
        btn_row = QHBoxLayout()
        self.play_btn    = QPushButton("▶ Play Now")
        self.queue_btn   = QPushButton("+ Add to Queue")
        self.add_pl_btn  = QPushButton("+ Add to Playlist")
        self.play_btn.clicked.connect(self._on_play)
        self.queue_btn.clicked.connect(self._on_queue)
        self.add_pl_btn.clicked.connect(self._on_add_to_playlist)
        btn_row.addWidget(self.play_btn)
        btn_row.addWidget(self.queue_btn)
        btn_row.addWidget(self.add_pl_btn)
        layout.addLayout(btn_row)

    # ── search ─────────────────────────────────────────────────────────────

    def do_search(self):
        q = self.search_input.text().strip()
        if not q: return
        self._status(f"Searching for '{q}'…", 5000)
        try:
            data = api_client.search(q)
        except BackendError as e:
            self._status(f"Search error: {e.detail}", 4000); return

        self.results_list.clear()
        for tr in data.get("tracks", []):
            self.results_list.addItem(make_track_item(
                tr.get("name", ""), tr.get("artists", ""),
                tr.get("duration_ms", 0), tr.get("uri"), tr.get("id"),
                tr.get("explicit", False),
            ))
        n = self.results_list.count()
        self._status(f"Found {n} results" if n else "No results found", 3000)

    # ── actions ────────────────────────────────────────────────────────────

    def _selected_uri(self) -> str | None:
        items = self.results_list.selectedItems()
        return items[0].data(Qt.UserRole) if items else None

    def _on_play(self):
        uri = self._selected_uri()
        if not uri: return
        try:
            api_client.play()
            api_client.add_to_queue(uri)
            api_client.next_track()
            self._status("Playing track ▶")
        except BackendError as e:
            self._status(f"Error: {e.detail}", 4000)
        self._refresh_playback()

    def _on_queue(self):
        uri = self._selected_uri()
        if not uri:
            self._status("Select a track first"); return
        self._queue_uri(uri)

    def _on_add_to_playlist(self):
        # reads current_playlist_id from the playlists tab via the window
        pid = (self._window.playlists_tab.current_playlist_id
               if self._window else None)
        if not pid:
            self._status("Select a playlist first (in Playlists tab)"); return
        uri = self._selected_uri()
        if not uri:
            self._status("Select a search result first"); return
        try:
            api_client.add_track_to_playlist(pid, uri)
            self._status("Added to playlist ✓")
        except BackendError as e:
            self._status(f"Error: {e.detail}", 4000)
