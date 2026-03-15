"""
GUI/app.py
Entry point — mirrors the ECP repo pattern: python GUI/app.py

Responsibilities (nothing more):
  1. Create QApplication
  2. Show startup splash
  3. Launch backend subprocess
  4. Wait for backend health check
  5. Show main window
  6. Tear down backend on exit
"""
import sys

from PySide6.QtCore    import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QVBoxLayout, QWidget

from GUI.core.launcher  import start_backend, wait_for_backend
from GUI.core.theme     import PALETTE
from GUI.main_window    import SpotifyPlayerWindow


# ── startup splash ────────────────────────────────────────────────────────

class _Splash(QWidget):
    """Minimal splash shown while the backend subprocess boots."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Desktop Control")
        self.setFixedSize(360, 140)
        self.setStyleSheet(
            f"background:{PALETTE['bg']}; color:{PALETTE['text']};"
        )
        self._dots = 0
        self.msg = QLabel("Starting backend")
        self.msg.setStyleSheet("font-size: 14px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 40, 32, 32)
        layout.addWidget(self.msg)

        timer = QTimer(self)
        timer.setInterval(380)
        timer.timeout.connect(self._tick)
        timer.start()

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self.msg.setText("Starting backend" + "." * self._dots)


# ── main ──────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Spotify Desktop Control")
    app.setStyle("Fusion")

    splash = _Splash()
    splash.show()
    app.processEvents()

    backend_proc = start_backend()

    if not wait_for_backend(timeout=15.0):
        splash.hide()
        QMessageBox.critical(
            None,
            "Backend failed to start",
            "The FastAPI backend did not respond within 15 seconds.\n\n"
            "• Check that backend/.env contains valid Spotify credentials.\n"
            "• Make sure port 8000 is not already in use.",
        )
        backend_proc.terminate()
        sys.exit(1)

    splash.hide()

    window = SpotifyPlayerWindow()
    window.show()

    exit_code = app.exec()

    try:
        backend_proc.terminate()
        backend_proc.wait(timeout=3)
    except Exception:
        pass

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
