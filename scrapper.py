import os
import requests
import base64
import threading
import json
import csv

class SpotifyScrapper:
    def __init__(self, logger):
        self.logger = logger
        self.lock = threading.Lock()

    def log(self, message, color="white"):
        self.logger.log_signal.emit(message, color)

    def start_scrap(self, config, finished_callback=None, save_as="json"):
        thread = threading.Thread(target=self.scrap_playlist, args=(config, finished_callback, save_as), daemon=True)
        thread.start()

    def scrap_playlist(self, config, finished_callback=None, save_as="json"):
        PLAYLIST_URL = config.get("playlist_url", "").strip()
        if "playlist/" in PLAYLIST_URL:
            PLAYLIST_ID = PLAYLIST_URL.split("playlist/")[1].split("?")[0]
        else:
            PLAYLIST_ID = PLAYLIST_URL

        CLIENT_ID = config.get("client_id", "").strip()
        CLIENT_SECRET = config.get("client_secret", "").strip()
        MARKET = config.get("market", "ES").strip()

        if not CLIENT_ID or not CLIENT_SECRET:
            self.log("[Error] Client ID or Client Secret not provided", "red")
            return

        try:
            self.log("[Scrapper] Requesting token...", "#ffca4e")
            auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
            b64_auth_str = base64.b64encode(auth_str.encode()).decode()
            token_url = "https://accounts.spotify.com/api/token"
            headers = {"Authorization": f"Basic {b64_auth_str}"}
            data = {"grant_type": "client_credentials"}
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            access_token = response.json()["access_token"]
            self.log("[Scrapper] Token obtained", "#ffca4e")

            headers = {"Authorization": f"Bearer {access_token}"}
            playlist_url = f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}"
            response = requests.get(playlist_url, headers=headers)
            response.raise_for_status()
            playlist_data = response.json()
            playlist_name = playlist_data["name"].strip()

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

            folder_path = os.path.join(os.getcwd(), "Scrapper")
            os.makedirs(folder_path, exist_ok=True)

            filename = os.path.join(folder_path, f"{playlist_name}.{save_as}")
            if save_as == "json":
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump({"playlist_name": playlist_name, "tracks": tracks}, f, ensure_ascii=False, indent=4)
                self.log(f"[Scrapper] JSON saved: {filename}", "#4eff6d")
            else:
                with open(filename, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["title", "artist", "url"])
                    writer.writeheader()
                    writer.writerows(tracks)
                self.log(f"[Scrapper] CSV saved: {filename}", "#4eff6d")

            if finished_callback:
                finished_callback()

        except Exception as e:
            self.log(f"[Error] {e}", "red")
