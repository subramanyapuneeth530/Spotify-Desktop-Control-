"""
GUI/core/utils.py
Pure utility functions used by widgets, tabs, and the main window.
No Qt widgets here — only logic that can be unit-tested in isolation.
"""
from typing import Optional
from PySide6.QtWidgets import QPushButton, QLabel, QListWidgetItem
from PySide6.QtCore    import Qt


def ms_to_mmss(ms: Optional[int]) -> str:
    """Convert milliseconds to MM:SS string."""
    if not ms or ms <= 0:
        return "--:--"
    s = int(ms / 1000)
    return f"{s // 60:02d}:{s % 60:02d}"


def detect_mood(text: str) -> str:
    """Return a mood key from track/album text for visual theming."""
    t = text.lower()
    if any(w in t for w in ["rock", "metal", "punk", "grunge", "hardcore"]):
        return "rock"
    if any(w in t for w in ["edm", "dance", "club", "remix", "house", "techno", "trance"]):
        return "edm"
    if any(w in t for w in ["chill", "lofi", "lo-fi", "sleep", "study", "ambient", "calm"]):
        return "chill"
    if any(w in t for w in ["jazz", "swing", "bossa", "blues", "soul"]):
        return "jazz"
    return "default"


def make_track_item(name: str, artists: str, duration_ms: int = 0,
                    uri: str = None, track_id: str = None,
                    explicit: bool = False) -> QListWidgetItem:
    """Build a QListWidgetItem for any track list (queue / playlists / search / library)."""
    dur  = f"  {ms_to_mmss(duration_ms)}" if duration_ms else ""
    exp  = " 🅴" if explicit else ""
    item = QListWidgetItem(f"{artists} — {name}{exp}{dur}")
    item.setData(Qt.UserRole,     uri)
    item.setData(Qt.UserRole + 1, track_id)
    item.setToolTip(f"{name}\n{artists}")
    return item


def icon_btn(text: str, tooltip: str = "") -> QPushButton:
    """Small circular icon button."""
    btn = QPushButton(text)
    btn.setObjectName("iconBtn")
    btn.setFixedSize(40, 40)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


def accent_btn(text: str) -> QPushButton:
    """Green accent-coloured button."""
    btn = QPushButton(text)
    btn.setObjectName("accentBtn")
    return btn


def section_label(text: str) -> QLabel:
    """Bold section heading label."""
    lbl = QLabel(text)
    lbl.setObjectName("heading")
    return lbl
