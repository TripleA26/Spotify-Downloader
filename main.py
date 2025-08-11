from PyQt6.QtWidgets import QApplication
from test_ui import SpotifyDownloaderUI

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = SpotifyDownloaderUI()
    window.show()
    sys.exit(app.exec())
