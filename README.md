# Spotify Playlist Downloader

A desktop application to download Spotify playlists as MP3 files using Spotify API and YouTube search.

---

## Features

- Authenticate with Spotify API using Client ID and Client Secret.
- Fetch and display playlist metadata.
- Download audio tracks from YouTube based on Spotify playlist info.
- Multi-threaded downloads with progress bar.
- Select custom FFMPEG executable for audio conversion.
- Simple and clean PyQt6-based user interface.

---

## Requirements

- Python 3.8+
- PyQt6
- requests
- yt-dlp

---

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/spotify-playlist-downloader.git
cd spotify-playlist-downloader
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Download [FFMPEG](https://ffmpeg.org/download.html) and note its path.

4. Run the app:

```bash
python main.py
```

---

## How to Use

1. Obtain Spotify API credentials:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
   - Create an app and get your Client ID and Client Secret.
2. Open the app and enter your Spotify Client ID and Client Secret in the **Configuration** tab.
3. Set your preferred market code (default is `ES`).
4. Select the path to your `ffmpeg.exe` binary.
5. Switch to the **Downloads** tab, enter a Spotify playlist URL, and click **Start Download**.
6. Monitor the progress and logs.
7. Downloaded MP3 files will be saved in a folder named after the playlist.

---

## Notes

- The app uses YouTube to fetch audio based on Spotify track info, so downloaded tracks depend on YouTube availability.
- Make sure `ffmpeg` is accessible or provide the full path.
- Downloading large playlists may take time; progress is limited to 5 concurrent downloads.

---

## License

This project is licensed under the MIT License.

---

## Acknowledgments

- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- PyQt6 community

---

## Contact

Created by TripleA26 - feel free to reach out!
@2a6a on discord
