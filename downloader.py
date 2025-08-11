import os
import requests
import base64
import yt_dlp
import threading
import time


class SpotifyDownloader:
    def __init__(self, logger):
        self.logger = logger
        self.total_tracks = 0
        self.completed_tracks = 0
        self.lock = threading.Lock()
        self.active_threads = []

    def log(self, message, color="white"):
        self.logger.log_signal.emit(message, color)

    def start_download(self, config, progress_callback, finished_callback):
        thread = threading.Thread(target=self.download_playlist, args=(config, progress_callback, finished_callback), daemon=True)
        thread.start()

    def download_playlist(self, config, progress_callback, finished_callback):
        CLIENT_ID = config.get("client_id")
        CLIENT_SECRET = config.get("client_secret")
        PLAYLIST_URL = config.get("playlist_url")
        MARKET = config.get("market", "ES")
        FFMPEG_PATH = config.get("ffmpeg_path")
        OUTPUT_JSON = "playlist.json"

        if "playlist/" in PLAYLIST_URL:
            PLAYLIST_ID = PLAYLIST_URL.split("playlist/")[1].split("?")[0]
        else:
            PLAYLIST_ID = PLAYLIST_URL

        try:
            self.log("[Token] Requesting token from Spotify...", "#ffca4e")
            auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
            b64_auth_str = base64.b64encode(auth_str.encode()).decode()
            token_url = "https://accounts.spotify.com/api/token"
            headers = {"Authorization": f"Basic {b64_auth_str}"}
            data = {"grant_type": "client_credentials"}
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            access_token = response.json()["access_token"]
            self.log("[Token] Successfully obtained access token", "#ffca4e")
        except Exception as e:
            self.log(f"[Error] Token request failed: {e}", "red")
            finished_callback()
            return

        try:
            self.log("[Playlist] Fetching playlist details...", "#ff6de3")
            playlist_url = f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}"
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(playlist_url, headers=headers)
            response.raise_for_status()
            playlist_data = response.json()

            playlist_name = playlist_data["name"].strip()
            if not os.path.exists(playlist_name):
                os.makedirs(playlist_name)

            tracks = []
            url = f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}/tracks"
            params = {"market": MARKET, "limit": 100}

            while url:
                r = requests.get(url, headers=headers, params=params)
                r.raise_for_status()
                data = r.json()
                for item in data["items"]:
                    track = item["track"]
                    if track:
                        tracks.append({
                            "title": track["name"],
                            "artist": ", ".join(a["name"] for a in track["artists"]),
                            "url": track["external_urls"]["spotify"]
                        })
                url = data["next"]
                params = None

            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                import json
                json.dump({"playlist_id": PLAYLIST_ID, "playlist_name": playlist_name, "total_tracks": len(tracks), "tracks": tracks}, f, ensure_ascii=False, indent=4)
            self.log(f"[Playlist] Saved metadata to {OUTPUT_JSON}", "#ff6de3")

            self.total_tracks = len(tracks)
            self.completed_tracks = 0
            progress_callback(self.completed_tracks, self.total_tracks)

            MAX_THREADS = 5
            self.active_threads = []

            for song in tracks:
                query = f"{song['title']} {song['artist']}"
                # Wait until threads < MAX_THREADS
                while True:
                    self.active_threads = [t for t in self.active_threads if t.is_alive()]
                    if len(self.active_threads) < MAX_THREADS:
                        break
                    time.sleep(0.5)

                t = threading.Thread(target=self.download_first_audio_mp3, args=(query, playlist_name, FFMPEG_PATH, progress_callback))
                t.start()
                self.active_threads.append(t)

            for t in self.active_threads:
                t.join()

            finished_callback()

        except Exception as e:
            self.log(f"[Error] Playlist download failed: {e}", "red")
            finished_callback()

    def download_first_audio_mp3(self, query, folder, ffmpeg_path, progress_callback):
        try:
            self.log(f"[Search] Looking for: {query}", "#5cb3ff")
            ydl_opts_search = {'quiet': True, 'extract_flat': True, 'default_search': 'ytsearch'}
            with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
                result = ydl.extract_info(f"ytsearch1:{query}", download=False)
                video_info = result['entries'][0]
            video_url = video_info['url']

            if ffmpeg_path and os.path.isfile(ffmpeg_path):
                ffmpeg_location = os.path.dirname(ffmpeg_path)
            else:
                ffmpeg_location = None

            ydl_opts_download = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'ffmpeg_location': ffmpeg_location,
            }
            with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                ydl.download([video_url])
            self.log(f"[Download] Finished: {query}", "#4eff6d")
        except Exception as e:
            self.log(f"[Error] {query}: {e}", "red")
        finally:
            with self.lock:
                self.completed_tracks += 1
                progress_callback(self.completed_tracks, self.total_tracks)
