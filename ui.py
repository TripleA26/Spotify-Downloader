from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QFileDialog, QTabWidget, QScrollArea, QProgressBar, QCheckBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QObject
from datetime import datetime
from downloader import SpotifyDownloader  # import downloader logic
from utils import get_styles, get_tab_styles, get_help_text
import ffmpeg_manager


class Logger(QObject):
    log_signal = pyqtSignal(str, str)


class SpotifyDownloaderUI(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = Logger()
        self.logger.log_signal.connect(self.append_log)

        self.setWindowTitle("Spotify Playlist Downloader")
        self.setGeometry(300, 200, 850, 550)
        self.setStyleSheet(get_styles())

        self.total_tracks = 0
        self.completed_tracks = 0

        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(get_tab_styles())

        config_tab = QWidget()
        config_layout = QVBoxLayout()

        self.client_id_input = self.create_input(config_layout, "CLIENT_ID:")
        self.client_secret_input = self.create_input(config_layout, "CLIENT_SECRET:", echo_mode=QLineEdit.EchoMode.Password)
        self.market_input = self.create_input(config_layout, "MARKET:", "ES")

        # Create ffmpeg input widgets inside a container widget
        self.ffmpeg_path_input = QLineEdit()
        self.ffmpeg_container = QWidget()
        ffmpeg_container_layout = QVBoxLayout()
        ffmpeg_container_layout.setContentsMargins(0, 0, 0, 0)

        self.ffmpeg_label = QLabel("FFMPEG_PATH:")
        self.ffmpeg_label.setStyleSheet("font-weight: bold;")
        ffmpeg_container_layout.addWidget(self.ffmpeg_label)
        ffmpeg_container_layout.addWidget(self.ffmpeg_path_input)
        self.ffmpeg_select_btn = QPushButton("Select FFMPEG")
        self.ffmpeg_select_btn.clicked.connect(self.select_ffmpeg_path)
        ffmpeg_container_layout.addWidget(self.ffmpeg_select_btn)
        self.ffmpeg_container.setLayout(ffmpeg_container_layout)
        config_layout.addWidget(self.ffmpeg_container)

        # Checkbox to toggle use of bundled ffmpeg
        self.use_bundled_ffmpeg_checkbox = QCheckBox("Use internal ffmpeg (bin/ffmpeg)")
        self.use_bundled_ffmpeg_checkbox.setChecked(True)
        config_layout.addWidget(self.use_bundled_ffmpeg_checkbox)

        # Connect checkbox toggle to show/hide ffmpeg widgets individually
        def toggle_ffmpeg_widgets(checked):
            visible = not checked
            self.ffmpeg_label.setVisible(visible)
            self.ffmpeg_path_input.setVisible(visible)
            self.ffmpeg_select_btn.setVisible(visible)

        self.use_bundled_ffmpeg_checkbox.toggled.connect(toggle_ffmpeg_widgets)
        # Initialize visibility properly based on initial checkbox state
        toggle_ffmpeg_widgets(self.use_bundled_ffmpeg_checkbox.isChecked())

        check_ffmpeg_btn = QPushButton("Verify / Download ffmpeg")
        check_ffmpeg_btn.clicked.connect(self.check_or_download_ffmpeg)
        config_layout.addWidget(check_ffmpeg_btn)

        config_tab.setLayout(config_layout)

        download_tab = QWidget()
        download_layout = QVBoxLayout()
        self.playlist_link_input = self.create_input(download_layout, "Playlist URL:")
        download_btn = QPushButton("Start Download")
        download_btn.clicked.connect(self.start_download)
        download_layout.addWidget(download_btn)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        download_layout.addWidget(self.progress_bar)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        download_layout.addWidget(self.log_area)
        download_tab.setLayout(download_layout)

        help_tab = QWidget()
        help_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        help_content_widget = QWidget()
        help_content_layout = QVBoxLayout()
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setStyleSheet("background-color: #1c1c2e; color: white; border: none;")
        help_text.setText(get_help_text())
        help_content_layout.addWidget(help_text)
        help_content_widget.setLayout(help_content_layout)
        scroll_area.setWidget(help_content_widget)
        help_layout.addWidget(scroll_area)
        help_tab.setLayout(help_layout)

        self.tabs.addTab(config_tab, "Configuration")
        self.tabs.addTab(download_tab, "Downloads")
        self.tabs.addTab(help_tab, "Help")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        # Downloader instance
        self.downloader = SpotifyDownloader(self.logger)

    def create_input(self, layout, label_text, default_value="", echo_mode=QLineEdit.EchoMode.Normal):
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; margin-top: 8px; margin-bottom: 2px;")
        layout.addWidget(label)
        line_edit = QLineEdit()
        line_edit.setText(default_value)
        line_edit.setEchoMode(echo_mode)
        layout.addWidget(line_edit)
        return line_edit

    def append_log(self, message, color="white"):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_area.append(f'<span style="color: gray;">{timestamp}</span> <span style="color: {color};">{message}</span>')
        with open("debug.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"{timestamp} {message}\n")

    def select_ffmpeg_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select FFMPEG", "", "Executable (*.exe)")
        if path:
            self.ffmpeg_path_input.setText(path)

    def start_download(self):
        playlist_url = self.playlist_link_input.text().strip()
        if not playlist_url:
            QMessageBox.warning(self, "Input Error", "Please enter a valid Playlist URL before starting the download.")
            return  # Stop here, don't start download

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        config = {
            "client_id": self.client_id_input.text().strip(),
            "client_secret": self.client_secret_input.text().strip(),
            "playlist_url": playlist_url,
            "market": self.market_input.text().strip(),
            "ffmpeg_path": self.ffmpeg_path_input.text().strip(),
        }

        self.downloader.start_download(config, self.update_progress, self.download_finished)

    def update_progress(self, completed, total):
        if total > 0:
            percentage = int((completed / total) * 100)
            self.progress_bar.setValue(percentage)

    def download_finished(self):
        self.append_log("[Finish] Playlist download completed.", "#00ffaa")
        self.progress_bar.setVisible(False)

    def check_or_download_ffmpeg(self):
        if ffmpeg_manager.is_ffmpeg_downloaded():
            QMessageBox.information(self, "FFmpeg", f"FFmpeg is already downloaded at:\n{ffmpeg_manager.get_ffmpeg_path()}")
            self.append_log(f"[FFmpeg] Already downloaded at:\n{ffmpeg_manager.get_ffmpeg_path()}", "#ffca4e")
        else:
            self.append_log("[FFmpeg] Not found. Downloading...", "#ffca4e")
            success = ffmpeg_manager.download_ffmpeg()
            if success:
                QMessageBox.information(self, "FFmpeg", "FFmpeg successfully downloaded.")
                self.append_log("[FFmpeg] Successfully downloaded.", "#ffca4e")
            else:
                QMessageBox.warning(self, "FFmpeg", "Could not download ffmpeg automatically. Install it manually.")
