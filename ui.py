from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
    QFileDialog, QTabWidget, QScrollArea, QProgressBar, QCheckBox, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QSettings
from datetime import datetime
from downloader import SpotifyDownloader
from utils import get_styles, get_tab_styles, get_help_text
from scrapper import SpotifyScrapper
import ffmpeg_manager
from export import Exporter
import glob
import os


class Logger(QObject):
    log_signal = pyqtSignal(str, str)


class ExportWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(str)

    def __init__(self, exporter, playlist_name, export_type, parent=None):
        super().__init__(parent)
        self.exporter = exporter
        self.playlist_name = playlist_name
        self.export_type = export_type

    def run(self):
        try:
            json_path = f"Scrapper/{self.playlist_name}.json"
            csv_path = f"Scrapper/{self.playlist_name}.csv"

            if os.path.exists(json_path):
                input_file = json_path
            elif os.path.exists(csv_path):
                input_file = csv_path
            else:
                self.finished.emit(f"[Error] Scrapper/{self.playlist_name}.json or .csv not found")
                return

            self.exporter.export_playlist(
                input_file,
                export_type=self.export_type,
                output_dir="Scrapper",
                progress_callback=lambda d, t: self.progress.emit(d, t)
            )

            self.finished.emit(f"[Export] {self.playlist_name} exported to {self.export_type}")
        except Exception as e:
            self.finished.emit(f"[Error Export] {e}")


class SpotifyDownloaderUI(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = Logger()

        self.setWindowTitle("Spotify Playlist Downloader")
        self.setGeometry(300, 200, 850, 550)
        self.setStyleSheet(get_styles())

        self.settings = QSettings("TripleTools", "SpotifyDownloader")

        self.total_tracks = 0
        self.completed_tracks = 0

        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(get_tab_styles())

        # ================= CONFIG TAB =================
        config_tab = QWidget()
        config_layout = QVBoxLayout()

        self.client_id_input = self.create_input(config_layout, "CLIENT_ID:")
        self.client_secret_input = self.create_input(config_layout, "CLIENT_SECRET:", echo_mode=QLineEdit.EchoMode.Password)
        self.market_input = self.create_input(config_layout, "MARKET:", "ES")

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

        self.use_bundled_ffmpeg_checkbox = QCheckBox("Use internal ffmpeg (bin/ffmpeg)")
        self.use_bundled_ffmpeg_checkbox.setChecked(True)
        config_layout.addWidget(self.use_bundled_ffmpeg_checkbox)

        def toggle_ffmpeg_widgets(checked):
            visible = not checked
            self.ffmpeg_label.setVisible(visible)
            self.ffmpeg_path_input.setVisible(visible)
            self.ffmpeg_select_btn.setVisible(visible)

        self.use_bundled_ffmpeg_checkbox.toggled.connect(toggle_ffmpeg_widgets)
        toggle_ffmpeg_widgets(self.use_bundled_ffmpeg_checkbox.isChecked())

        check_ffmpeg_btn = QPushButton("Verify / Download ffmpeg")
        check_ffmpeg_btn.clicked.connect(self.check_or_download_ffmpeg)
        config_layout.addWidget(check_ffmpeg_btn)
        config_tab.setLayout(config_layout)
        self.load_settings()

        # ================= EXPORT TAB =================
        self.exporter = Exporter(self.logger)
        export_tab = QWidget()
        export_layout = QVBoxLayout()

        self.export_progress = QProgressBar()
        self.export_progress.setVisible(False)
        export_layout.addWidget(self.export_progress)

        self.export_log = QTextEdit()
        self.export_log.setReadOnly(True)
        export_layout.addWidget(self.export_log)

        buttons_layout = QHBoxLayout()
        export_json_btn = QPushButton("Export JSON")
        export_csv_btn = QPushButton("Export CSV")
        export_json_btn.clicked.connect(lambda: self.start_export("json"))
        export_csv_btn.clicked.connect(lambda: self.start_export("csv"))
        buttons_layout.addWidget(export_json_btn)
        buttons_layout.addWidget(export_csv_btn)
        export_layout.addLayout(buttons_layout)
        export_tab.setLayout(export_layout)

        # ================= PLAYLIST TAB =================
        playlist_tab = QWidget()
        playlist_layout = QVBoxLayout()

        self.playlist_link_input = self.create_input(playlist_layout, "Playlist URL:")

        download_btn = QPushButton("Start Download")
        download_btn.clicked.connect(self.start_download)
        playlist_layout.addWidget(download_btn)

        scrap_layout = QHBoxLayout()
        scrap_json_btn = QPushButton("Scrap JSON")
        scrap_csv_btn = QPushButton("Scrap CSV")
        scrap_json_btn.clicked.connect(lambda: self.scrap_playlist(save_as="json"))
        scrap_csv_btn.clicked.connect(lambda: self.scrap_playlist(save_as="csv"))
        scrap_layout.addWidget(scrap_json_btn)
        scrap_layout.addWidget(scrap_csv_btn)
        playlist_layout.addLayout(scrap_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        playlist_layout.addWidget(self.progress_bar)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        playlist_layout.addWidget(self.log_area)
        playlist_tab.setLayout(playlist_layout)

        # ================= HELP TAB =================
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

        # ================= TABS =================
        self.tabs.addTab(config_tab, "Configuration")
        self.tabs.addTab(playlist_tab, "Playlist")
        self.tabs.addTab(export_tab, "Export")
        self.tabs.addTab(help_tab, "Help")
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        self.downloader = SpotifyDownloader(self.logger)
        self.logger.log_signal.connect(self.append_log)

    # ================= UTILIDADES =================
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
        formatted = f'<span style="color: gray;">{timestamp}</span> <span style="color: {color};">{message}</span>'
        self.log_area.append(formatted)
        self.export_log.append(formatted)
        with open("debug.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"{timestamp} {message}\n")

    def select_ffmpeg_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select FFMPEG", "", "Executable (*.exe)")
        if path:
            self.ffmpeg_path_input.setText(path)

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

    # ================= MAIN FUNCTIONS =================
    def start_download(self):
        playlist_url = self.playlist_link_input.text().strip()
        if not playlist_url:
            QMessageBox.warning(self, "Input Error", "Please enter a valid Playlist URL before starting the download.")
            return

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

    def scrap_playlist(self, save_as="json"):
        playlist_url = self.playlist_link_input.text().strip()
        if not playlist_url:
            QMessageBox.warning(self, "Input Error", "Please enter a valid Playlist URL before scrapping.")
            return

        config = {
            "client_id": self.client_id_input.text().strip(),
            "client_secret": self.client_secret_input.text().strip(),
            "playlist_url": playlist_url,
            "market": self.market_input.text().strip(),
        }

        scrapper = SpotifyScrapper(self.logger)
        scrapper.start_scrap(config, save_as=save_as)

    def start_export(self, export_type: str):
        json_files = glob.glob("Scrapper/*.json")
        csv_files = glob.glob("Scrapper/*.csv")
        all_files = json_files + csv_files

        if not all_files:
            self.append_log("[Error] No playlist JSON/CSV found in Scrapper/", "red")
            return

        input_file = all_files[0]
        playlist_name = os.path.splitext(os.path.basename(input_file))[0]

        self.append_log(f"[Export] Starting export of {playlist_name} -> {export_type}", "#5cb3ff")

        self.export_thread = ExportWorker(self.exporter, playlist_name, export_type)
        self.export_thread.progress.connect(self.update_export_progress)
        self.export_thread.finished.connect(self.export_finished)

        self.export_progress.setVisible(True)
        self.export_progress.setValue(0)
        self.export_thread.start()

    def update_export_progress(self, done, total):
        if total > 0:
            percent = int((done / total) * 100)
            self.export_progress.setValue(percent)

    def export_finished(self, msg):
        self.append_log(msg, "#4eff6d")
        self.export_progress.setVisible(False)

    # ================= SETTINGS =================
    def load_settings(self):
        self.client_id_input.setText(self.settings.value("client_id", ""))
        self.client_secret_input.setText(self.settings.value("client_secret", ""))
        self.market_input.setText(self.settings.value("market", "ES"))
        self.ffmpeg_path_input.setText(self.settings.value("ffmpeg_path", ""))

    def save_settings(self):
        self.settings.setValue("client_id", self.client_id_input.text())
        self.settings.setValue("client_secret", self.client_secret_input.text())
        self.settings.setValue("market", self.market_input.text())
        self.settings.setValue("ffmpeg_path", self.ffmpeg_path_input.text())

    def closeEvent(self, event):
        self.save_settings()
        event.accept()
