"""
GUI/main_window.py
The main application window.
Owns the left column (cassette + controls) and the right tab panel.
All tab logic lives in GUI/tabs/; all state that tabs need is exposed
as plain attributes so tabs can read them without circular imports.
"""
from __future__ import annotations

import json
from typing import Optional

from PySide6.QtCore    import Qt, QTimer, QUrl
from PySide6.QtGui     import QColor, QFont, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QSlider, QSplitter, QStatusBar, QTabWidget,
    QVBoxLayout, QWidget,
)

from GUI.core            import api_client
from GUI.core.api_client import BackendError, BASE_URL
from GUI.core.theme      import BASE_QSS, PALETTE
from GUI.core.utils      import detect_mood, icon_btn, ms_to_mmss
from GUI.widgets.cassette_widget import CassetteWidget
from GUI.tabs.queue_tab      import QueueTab
from GUI.tabs.playlists_tab  import PlaylistsTab
from GUI.tabs.search_tab     import SearchTab
from GUI.tabs.library_tab    import LibraryTab


class SpotifyPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Desktop Control")
        self.setMinimumSize(920, 700)
        self.resize(1100, 760)
        self.setStyleSheet(BASE_QSS)

        # ── shared state (tabs read these) ──────────────────────────────
        self.current_track_uri:       Optional[str] = None
        self.current_track_id:        Optional[str] = None
        self.current_track_duration_ms: int         = 0
        self.last_track_id:           Optional[str] = None
        self._last_is_playing:        bool          = False
        self._slider_dragging:        bool          = False
        self._is_liked:               bool          = False
        self._playback_in_flight:     bool          = False
        self._pending_album_url:      Optional[str] = None

        # ── async networking ────────────────────────────────────────────
        self.playback_net = QNetworkAccessManager(self)
        self.playback_net.finished.connect(self._on_playback_reply)
        self.album_net = QNetworkAccessManager(self)
        self.album_net.finished.connect(self._on_album_reply)

        self._build_ui()
        self._setup_timers()

        # deferred initial loads — window paints before data arrives
        QTimer.singleShot(200,  self.fetch_playback)
        QTimer.singleShot(400,  self.load_devices)
        QTimer.singleShot(600,  self.playlists_tab.load_playlists)

    # ─────────────────────────────── UI BUILD ───────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        # ── cassette (now-playing) widget ────────────────────────────────
        self.cassette = CassetteWidget()
        self.cassette.setMinimumWidth(280)
        self.cassette.setMaximumWidth(420)

        # ── transport controls ───────────────────────────────────────────
        controls = self._build_controls()

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(12)
        left_col.addWidget(self.cassette, stretch=1)
        left_col.addLayout(controls)

        left_widget = QWidget()
        left_widget.setLayout(left_col)

        # ── right panel: tabs ────────────────────────────────────────────
        self._build_tabs()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 700])
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {PALETTE['border']}; }}"
        )

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 4)
        main_layout.setSpacing(0)
        main_layout.addWidget(splitter)

        # ── status bar ───────────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _build_controls(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # track label + like button
        self.track_label = QLabel("No track playing")
        self.track_label.setAlignment(Qt.AlignCenter)
        self.track_label.setWordWrap(True)
        f = self.track_label.font(); f.setPointSize(12)
        self.track_label.setFont(f)

        self.like_btn = icon_btn("♡", "Like / Unlike track")
        self.like_btn.clicked.connect(self._on_like_clicked)

        like_row = QHBoxLayout()
        like_row.addStretch()
        like_row.addWidget(self.track_label)
        like_row.addWidget(self.like_btn)
        like_row.addStretch()

        # progress slider + time
        self.time_label = QLabel("--:-- / --:--")
        self.time_label.setObjectName("sub")
        self.time_label.setAlignment(Qt.AlignCenter)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderPressed.connect(
            lambda: setattr(self, '_slider_dragging', True))
        self.progress_slider.sliderReleased.connect(self._on_seek)

        # transport buttons
        self.shuffle_btn = icon_btn("⇄", "Shuffle"); self.shuffle_btn.setCheckable(True)
        self.prev_btn    = icon_btn("⏮", "Previous")
        self.play_btn    = QPushButton("▶")
        self.play_btn.setFixedSize(52, 52)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PALETTE['accent']}; color: #000;
                border: none; border-radius: 26px;
                font-size: 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {PALETTE['accent2']}; }}
        """)
        self.next_btn   = icon_btn("⏭", "Next")
        self.repeat_btn = icon_btn("↺", "Repeat"); self.repeat_btn.setCheckable(True)

        self.shuffle_btn.clicked.connect(self._on_shuffle)
        self.prev_btn.clicked.connect(self._on_prev)
        self.play_btn.clicked.connect(self._on_play_pause)
        self.next_btn.clicked.connect(self._on_next)
        self.repeat_btn.clicked.connect(self._on_repeat)

        btn_row = QHBoxLayout(); btn_row.setSpacing(4)
        btn_row.addStretch()
        for w in [self.shuffle_btn, self.prev_btn, self.play_btn,
                  self.next_btn, self.repeat_btn]:
            btn_row.addWidget(w)
        btn_row.addStretch()

        # volume
        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("🔊"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100); self.volume_slider.setValue(50)
        self.volume_slider.sliderReleased.connect(self._on_volume_changed)
        self.vol_label = QLabel("50%")
        self.vol_label.setObjectName("sub"); self.vol_label.setFixedWidth(36)
        self.volume_slider.valueChanged.connect(
            lambda v: self.vol_label.setText(f"{v}%"))
        vol_row.addWidget(self.volume_slider)
        vol_row.addWidget(self.vol_label)

        # device
        dev_row = QHBoxLayout()
        dev_lbl = QLabel("Device"); dev_lbl.setObjectName("sub")
        self.device_combo = QComboBox()
        self.refresh_dev_btn = QPushButton("↻")
        self.refresh_dev_btn.setFixedSize(32, 32)
        self.refresh_dev_btn.setToolTip("Refresh devices")
        self.refresh_dev_btn.clicked.connect(self.load_devices)
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        dev_row.addWidget(dev_lbl)
        dev_row.addWidget(self.device_combo, stretch=1)
        dev_row.addWidget(self.refresh_dev_btn)

        for item in [like_row, None, self.progress_slider, self.time_label,
                     btn_row, vol_row, dev_row]:
            if item is None:
                pass
            elif isinstance(item, QHBoxLayout):
                layout.addLayout(item)
            else:
                layout.addWidget(item)
        return layout

    def _build_tabs(self):
        self.queue_tab     = QueueTab()
        self.playlists_tab = PlaylistsTab()
        self.search_tab    = SearchTab()
        self.library_tab   = LibraryTab()

        for tab in [self.queue_tab, self.playlists_tab,
                    self.search_tab, self.library_tab]:
            tab._set_window(self)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.queue_tab,     "Queue")
        self.tab_widget.addTab(self.playlists_tab, "Playlists")
        self.tab_widget.addTab(self.search_tab,    "Search")
        self.tab_widget.addTab(self.library_tab,   "Library")

    # ─────────────────────────────── TIMERS ─────────────────────────────────

    def _setup_timers(self):
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(2000)
        self.poll_timer.timeout.connect(self.fetch_playback)
        self.poll_timer.start()

        self._status_clear = QTimer(self)
        self._status_clear.setSingleShot(True)
        self._status_clear.timeout.connect(lambda: self.status_bar.showMessage(""))

    def show_status(self, msg: str, ms: int = 3000):
        """Called by tabs and other components to write to the status bar."""
        self.status_bar.showMessage(msg)
        self._status_clear.start(ms)

    # ─────────────────────────── ASYNC PLAYBACK ─────────────────────────────

    def fetch_playback(self):
        if self._playback_in_flight:
            return
        self._playback_in_flight = True
        self.playback_net.get(QNetworkRequest(QUrl(f"{BASE_URL}/playback/state")))

    def _on_playback_reply(self, reply):
        self._playback_in_flight = False
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                return
            raw = bytes(reply.readAll())
            self._apply_state(json.loads(raw.decode("utf-8")) if raw else {})
        except Exception as e:
            self.show_status(f"Playback error: {e}", 4000)
        finally:
            reply.deleteLater()

    def _apply_state(self, state: dict):
        item       = state.get("item")
        is_playing = state.get("is_playing", False)
        self._last_is_playing = is_playing
        self.play_btn.setText("⏸" if is_playing else "▶")

        if not item:
            self.track_label.setText("Nothing playing")
            self.time_label.setText("--:-- / --:--")
            self.progress_slider.setValue(0)
            self.cassette.set_playing_state(False)
            self.cassette.update_track("", "", "", 0, 0)
            return

        name      = item.get("name", "Unknown")
        artists   = ", ".join(a["name"] for a in item.get("artists", []))
        album     = (item.get("album") or {}).get("name", "")
        track_id  = item.get("id")
        self.current_track_uri = item.get("uri")
        self.current_track_id  = track_id

        progress_ms = state.get("progress_ms") or 0
        duration_ms = item.get("duration_ms")  or 0
        self.current_track_duration_ms = duration_ms

        mood = detect_mood(f"{name} {album}".lower())
        self.track_label.setText(f"{name} — {artists}")
        self.time_label.setText(f"{ms_to_mmss(progress_ms)} / {ms_to_mmss(duration_ms)}")

        if not self._slider_dragging and duration_ms > 0:
            self.progress_slider.blockSignals(True)
            self.progress_slider.setValue(int(progress_ms / duration_ms * 1000))
            self.progress_slider.blockSignals(False)

        vol = (state.get("device") or {}).get("volume_percent")
        if vol is not None:
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(vol)
            self.volume_slider.blockSignals(False)

        sh = state.get("shuffle_state", False)
        self.shuffle_btn.setChecked(sh)
        self.shuffle_btn.setStyleSheet(
            f"color: {PALETTE['accent']};" if sh else "")

        # update cassette hue every tick so RGB keeps cycling
        self.cassette.set_playing_state(is_playing)
        self.cassette.update_track(name, artists, album,
                                   progress_ms, duration_ms, mood)

        if track_id != self.last_track_id:
            images = (item.get("album") or {}).get("images") or []
            self._fetch_album_art(images[0]["url"] if images else None)
            self.queue_tab.load()
            self._check_liked(track_id)
            self.last_track_id = track_id

    # ─────────────────────────── ASYNC ALBUM ART ────────────────────────────

    def _fetch_album_art(self, url: Optional[str]):
        if not url or url == self._pending_album_url:
            return
        self._pending_album_url = url
        self.album_net.get(QNetworkRequest(QUrl(url)))

    def _on_album_reply(self, reply):
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                return
            pix = QPixmap()
            pix.loadFromData(bytes(reply.readAll()))
            self.cassette.set_album_art(pix)
        finally:
            reply.deleteLater()

    # ─────────────────────────── TRANSPORT CONTROLS ─────────────────────────

    def _on_play_pause(self):
        try:
            api_client.pause() if self._last_is_playing else api_client.play()
        except BackendError as e:
            self.show_status(f"Error: {e.detail}", 4000)
        self.fetch_playback()

    def _on_prev(self):
        try:    api_client.previous_track()
        except BackendError as e: self.show_status(f"Error: {e.detail}", 4000)
        QTimer.singleShot(400, self.fetch_playback)

    def _on_next(self):
        try:    api_client.next_track()
        except BackendError as e: self.show_status(f"Error: {e.detail}", 4000)
        QTimer.singleShot(400, self.fetch_playback)

    def _on_seek(self):
        self._slider_dragging = False
        if self.current_track_duration_ms <= 0:
            return
        pos = int(self.progress_slider.value() / 1000 * self.current_track_duration_ms)
        try:    api_client.seek(pos)
        except BackendError as e: self.show_status(f"Seek error: {e.detail}", 4000)
        QTimer.singleShot(300, self.fetch_playback)

    def _on_volume_changed(self):
        v = self.volume_slider.value()
        try:    api_client.set_volume(v); self.show_status(f"Volume: {v}%", 1500)
        except BackendError as e: self.show_status(f"Volume error: {e.detail}", 4000)

    def _on_shuffle(self, checked: bool):
        try:
            api_client.set_shuffle(checked)
            self.shuffle_btn.setStyleSheet(
                f"color: {PALETTE['accent']};" if checked else "")
            self.show_status("Shuffle " + ("on" if checked else "off"), 1500)
        except BackendError as e: self.show_status(f"Shuffle error: {e.detail}", 4000)

    def _on_repeat(self, checked: bool):
        mode = "context" if checked else "off"
        try:
            api_client.set_repeat(mode)
            self.repeat_btn.setStyleSheet(
                f"color: {PALETTE['accent']};" if checked else "")
            self.show_status(f"Repeat: {mode}", 1500)
        except BackendError as e: self.show_status(f"Repeat error: {e.detail}", 4000)

    # ─────────────────────────── LIKE ───────────────────────────────────────

    def _check_liked(self, track_id: str):
        try:
            self._is_liked = api_client.is_track_liked(track_id)
            self.like_btn.setText("♥" if self._is_liked else "♡")
            self.like_btn.setStyleSheet(
                f"color: {PALETTE['accent']}; font-size: 18px;"
                if self._is_liked else "font-size: 18px;")
        except Exception:
            pass

    def _on_like_clicked(self):
        if not self.current_track_id:
            return
        try:
            if self._is_liked:
                api_client.unlike_track(self.current_track_id)
                self._is_liked = False
                self.show_status("Removed from Liked Songs")
            else:
                api_client.like_track(self.current_track_id)
                self._is_liked = True
                self.show_status("Added to Liked Songs ♥")
            self.like_btn.setText("♥" if self._is_liked else "♡")
            self.like_btn.setStyleSheet(
                f"color: {PALETTE['accent']}; font-size: 18px;"
                if self._is_liked else "font-size: 18px;")
        except BackendError as e:
            self.show_status(f"Error: {e.detail}", 4000)

    # ─────────────────────────── DEVICES ────────────────────────────────────

    def load_devices(self):
        try:
            data = api_client.get_devices()
        except BackendError as e:
            self.show_status(f"Device error: {e.detail}", 4000); return

        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        for d in data.get("devices", []):
            label = d.get("name", "Unknown")
            if d.get("is_active"): label += " ●"
            self.device_combo.addItem(label, userData=d.get("id"))
        self.device_combo.blockSignals(False)

    def _on_device_changed(self, index: int):
        did = self.device_combo.itemData(index)
        if not did: return
        try:
            api_client.transfer_playback(did)
            self.show_status("Switched device")
        except BackendError as e:
            self.show_status(f"Device error: {e.detail}", 4000)
