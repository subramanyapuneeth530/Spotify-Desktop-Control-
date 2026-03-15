"""
GUI/tabs/queue_tab.py
Shows the Spotify queue (up-next tracks).
"""
from PySide6.QtWidgets import QVBoxLayout, QListWidget, QPushButton

from GUI.tabs.base_tab  import BaseTab
from GUI.core           import api_client
from GUI.core.api_client import BackendError
from GUI.core.utils     import section_label, make_track_item


class QueueTab(BaseTab):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(section_label("Up Next"))

        self.queue_list = QListWidget()
        layout.addWidget(self.queue_list)

        refresh_btn = QPushButton("↻  Refresh Queue")
        refresh_btn.clicked.connect(self.load)
        layout.addWidget(refresh_btn)

    def load(self):
        try:
            data = api_client.get_queue()
        except BackendError as e:
            self._status(f"Queue error: {e.detail}", 3000)
            return

        self.queue_list.clear()
        for tr in data.get("queue", []):
            self.queue_list.addItem(make_track_item(
                tr.get("name", ""), tr.get("artists", ""),
                tr.get("duration_ms", 0), tr.get("uri"), tr.get("id"),
            ))
