"""
GUI/core/theme.py
Single source of truth for colours and stylesheets.
Import PALETTE or BASE_QSS anywhere in the GUI — never hardcode colours.
"""

PALETTE = {
    "bg":       "#0a0a0f",
    "surface":  "#12121a",
    "surface2": "#1a1a26",
    "border":   "#2a2a3a",
    "accent":   "#1db954",   # Spotify green
    "accent2":  "#1ed760",
    "text":     "#f0f0f0",
    "subtext":  "#a0a0b0",
    "danger":   "#e05555",
    "warning":  "#e8a040",
}

BASE_QSS = f"""
QMainWindow, QWidget {{
    background-color: {PALETTE['bg']};
    color: {PALETTE['text']};
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}}
QTabWidget::pane {{
    border: 1px solid {PALETTE['border']};
    border-radius: 8px;
    background: {PALETTE['surface']};
}}
QTabBar::tab {{
    background: {PALETTE['surface']};
    color: {PALETTE['subtext']};
    border: 1px solid {PALETTE['border']};
    border-bottom: none;
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
    min-width: 90px;
}}
QTabBar::tab:selected {{
    background: {PALETTE['surface2']};
    color: {PALETTE['text']};
    border-color: {PALETTE['accent']};
}}
QTabBar::tab:hover:!selected {{
    background: {PALETTE['surface2']};
    color: {PALETTE['text']};
}}
QPushButton {{
    background: {PALETTE['surface2']};
    color: {PALETTE['text']};
    border: 1px solid {PALETTE['border']};
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 500;
}}
QPushButton:hover  {{ background: #252535; border-color: {PALETTE['accent']}; }}
QPushButton:pressed {{ background: #1a1a28; }}
QPushButton:disabled {{ color: #555568; border-color: #222230; }}
QPushButton#accentBtn {{
    background: {PALETTE['accent']}; color: #000;
    border: none; font-weight: 700;
}}
QPushButton#accentBtn:hover {{ background: {PALETTE['accent2']}; }}
QPushButton#iconBtn {{
    background: transparent; border: none;
    border-radius: 20px; padding: 6px; font-size: 18px;
}}
QPushButton#iconBtn:hover {{ background: rgba(255,255,255,0.08); }}
QSlider::groove:horizontal {{
    background: {PALETTE['border']}; height: 4px; border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {PALETTE['accent']}; height: 4px; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: #fff; border: 2px solid {PALETTE['accent']};
    width: 12px; height: 12px; margin: -5px 0; border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: {PALETTE['accent']};
    width: 14px; height: 14px; margin: -6px 0; border-radius: 8px;
}}
QListWidget {{
    background: {PALETTE['surface']};
    border: 1px solid {PALETTE['border']};
    border-radius: 8px; outline: none; padding: 4px;
}}
QListWidget::item {{ border-radius: 6px; padding: 6px 8px; color: {PALETTE['text']}; }}
QListWidget::item:selected {{
    background: rgba(29,185,84,0.15); color: #fff;
    border: 1px solid rgba(29,185,84,0.4);
}}
QListWidget::item:hover:!selected {{ background: {PALETTE['surface2']}; }}
QComboBox {{
    background: {PALETTE['surface2']}; border: 1px solid {PALETTE['border']};
    border-radius: 8px; padding: 6px 12px;
    color: {PALETTE['text']}; min-width: 130px;
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {PALETTE['surface2']}; border: 1px solid {PALETTE['border']};
    color: {PALETTE['text']}; selection-background-color: rgba(29,185,84,0.2);
}}
QLineEdit {{
    background: {PALETTE['surface2']}; border: 1px solid {PALETTE['border']};
    border-radius: 8px; padding: 8px 14px;
    color: {PALETTE['text']}; font-size: 13px;
}}
QLineEdit:focus {{ border-color: {PALETTE['accent']}; }}
QLabel {{ color: {PALETTE['text']}; background: transparent; }}
QLabel#sub     {{ color: {PALETTE['subtext']}; font-size: 12px; }}
QLabel#heading {{ font-size: 15px; font-weight: 700; color: {PALETTE['text']}; }}
QProgressBar {{
    background: {PALETTE['border']}; border: none;
    border-radius: 3px; height: 4px;
}}
QProgressBar::chunk {{ background: {PALETTE['accent']}; border-radius: 3px; }}
QScrollBar:vertical {{ background: transparent; width: 6px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {PALETTE['border']}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QStatusBar {{
    background: {PALETTE['surface']}; border-top: 1px solid {PALETTE['border']};
    color: {PALETTE['subtext']}; font-size: 12px; padding: 4px 8px;
}}
"""
