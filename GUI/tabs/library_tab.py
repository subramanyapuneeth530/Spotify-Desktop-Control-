"""
GUI/tabs/library_tab.py
Liked Songs and Recently Played — two sub-tabs inside a QTabWidget.
"""
from PySide6.QtCore    import Qt, QTimer
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QTabWidget, QWidget,
)

from GUI.tabs.base_tab   import BaseTab
from GUI.core            import api_client
from GUI.core.api_client import BackendError
from GUI.core.utils      import section_label, make_track_item


class LibraryTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        sub = QTabWidget()

        # ── liked songs ───────────────────────────────────────────────────
        liked_w = QWidget()
        liked_l = QVBoxLayout(liked_w)
        liked_l.setContentsMargins(8, 8, 8, 8)
        liked_l.addWidget(section_label("Liked Songs"))
        self.liked_list = QListWidget()
        self.liked_list.itemDoubleClicked.connect(self._on_liked_play)
        liked_l.addWidget(self.liked_list)
        liked_btns = QHBoxLayout()
        self.liked_play_btn    = QPushButton("▶ Play")
        self.liked_queue_btn   = QPushButton("+ Queue")
        self.liked_refresh_btn = QPushButton("↻ Refresh")
        self.liked_play_btn.clicked.connect(self._on_liked_play)
        self.liked_queue_btn.clicked.connect(self._on_liked_queue)
        self.liked_refresh_btn.clicked.connect(self.load_liked)
        liked_btns.addWidget(self.liked_play_btn)
        liked_btns.addWidget(self.liked_queue_btn)
        liked_btns.addWidget(self.liked_refresh_btn)
        liked_l.addLayout(liked_btns)

        # ── recently played ───────────────────────────────────────────────
        recent_w = QWidget()
        recent_l = QVBoxLayout(recent_w)
        recent_l.setContentsMargins(8, 8, 8, 8)
        recent_l.addWidget(section_label("Recently Played"))
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self._on_recent_play)
        recent_l.addWidget(self.recent_list)
        recent_btns = QHBoxLayout()
        self.recent_play_btn    = QPushButton("▶ Play")
        self.recent_queue_btn   = QPushButton("+ Queue")
        self.recent_refresh_btn = QPushButton("↻ Refresh")
        self.recent_play_btn.clicked.connect(self._on_recent_play)
        self.recent_queue_btn.clicked.connect(self._on_recent_queue)
        self.recent_refresh_btn.clicked.connect(self.load_recent)
        recent_btns.addWidget(self.recent_play_btn)
        recent_btns.addWidget(self.recent_queue_btn)
        recent_btns.addWidget(self.recent_refresh_btn)
        recent_l.addLayout(recent_btns)

        sub.addTab(liked_w,  "❤ Liked Songs")
        sub.addTab(recent_w, "🕐 Recently Played")
        layout.addWidget(sub)

        # defer initial load so the window paints first
        QTimer.singleShot(800,  self.load_liked)
        QTimer.singleShot(1000, self.load_recent)

    # ── data loading ───────────────────────────────────────────────────────

    def load_liked(self):
        try:
            data = api_client.get_liked_songs(limit=50)
        except BackendError as e:
            self._status(f"Liked songs error: {e.detail}", 4000); return
        self.liked_list.clear()
        for tr in data.get("tracks", []):
            self.liked_list.addItem(make_track_item(
                tr.get("name", ""), tr.get("artists", ""),
                0, tr.get("uri"), tr.get("id"),
            ))

    def load_recent(self):
        try:
            data = api_client.get_recently_played()
        except BackendError as e:
            self._status(f"Recent error: {e.detail}", 4000); return
        self.recent_list.clear()
        seen: set[str] = set()
        for tr in data.get("tracks", []):
            tid = tr.get("id")
            if tid in seen: continue
            seen.add(tid)
            self.recent_list.addItem(make_track_item(
                tr.get("name", ""), tr.get("artists", ""),
                0, tr.get("uri"), tid,
            ))

    # ── liked callbacks ────────────────────────────────────────────────────

    def _on_liked_play(self):
        items = self.liked_list.selectedItems()
        if items: self._queue_and_skip(items[0].data(Qt.UserRole))

    def _on_liked_queue(self):
        items = self.liked_list.selectedItems()
        if not items: self._status("Select a track first"); return
        self._queue_uri(items[0].data(Qt.UserRole))

    # ── recent callbacks ───────────────────────────────────────────────────

    def _on_recent_play(self):
        items = self.recent_list.selectedItems()
        if items: self._queue_and_skip(items[0].data(Qt.UserRole))

    def _on_recent_queue(self):
        items = self.recent_list.selectedItems()
        if not items: self._status("Select a track first"); return
        self._queue_uri(items[0].data(Qt.UserRole))
