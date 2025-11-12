import os
import json
import csv
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed

class Exporter:
    def __init__(self, logger):
        self.logger = logger

    def log(self, message, color="white"):
        if self.logger:
            self.logger.log_signal.emit(message, color)

    def get_first_youtube_url(self, query):
        try:
            ydl_opts_search = {
                'quiet': True,
                'extract_flat': True,
                'default_search': 'ytsearch'
            }
            with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
                result = ydl.extract_info(f"ytsearch1:{query}", download=False)
                video_info = result['entries'][0]
            return video_info['url']
        except Exception as e:
            self.log(f"[Error URL] {query}: {e}", "red")
            return None

    def export_playlist(self, input_file, export_type="json", output_dir=".", max_workers=5, progress_callback=None):
    # Detect file type
        if input_file.endswith(".json"):
            with open(input_file, "r", encoding="utf-8") as f:
                playlist = json.load(f)
        elif input_file.endswith(".csv"):
            playlist = {
                "playlist_name": os.path.splitext(os.path.basename(input_file))[0],
                "tracks": []
            }
            with open(input_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    playlist["tracks"].append({
                        "title": row["title"],
                        "artist": row["artist"],
                        "spotify_url": row.get("url", "")
                    })
        else:
            self.log(f"[Error] Unsupported file format: {input_file}", "red")
            return

        safe_name = playlist["playlist_name"].replace(" ", "_")
        filename = f"{safe_name}_ExportYT.{export_type}"
        output_path = os.path.join(output_dir, filename)

        export_data = {
            "playlist_name": playlist["playlist_name"],
            "tracks": []
        }

        total = len(playlist["tracks"])
        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.get_first_youtube_url, f"{t['title']} {t['artist']}"): t
                for t in playlist["tracks"]
            }

            for future in as_completed(futures):
                track = futures[future]
                youtube_url = future.result()
                export_data["tracks"].append({
                    "title": track["title"],
                    "artist": track["artist"],
                    "youtube_url": youtube_url
                })

                completed += 1
                self.log(f"[Export] {track['title']} - {track['artist']}", "#4eff6d")
                if progress_callback:
                    progress_callback(completed, total) 

        # Save JSON
        if export_type == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)

        # Save CSV
        elif export_type == "csv":
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Title", "Artist", "YouTube URL"])
                for t in export_data["tracks"]:
                    writer.writerow([t["title"], t["artist"], t["youtube_url"]])

        self.log(f"[Export] Playlist exported in: {output_path}", "#00ffaa")
