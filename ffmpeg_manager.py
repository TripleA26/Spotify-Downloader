import os
import sys
import urllib.request
import zipfile
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")
FFMPEG_EXE = "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"
FFMPEG_PATH = os.path.join(BIN_DIR, FFMPEG_EXE)

def is_ffmpeg_downloaded():
    return os.path.isfile(FFMPEG_PATH)

def download_ffmpeg():
    os.makedirs(BIN_DIR, exist_ok=True)

    if sys.platform.startswith("win"):
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    else:
        print("Only Windows supported for automatic download. Please install ffmpeg manually.")
        return False

    zip_path = os.path.join(BIN_DIR, "ffmpeg.zip")
    print("Downloading ffmpeg...")
    urllib.request.urlretrieve(url, zip_path)
    print("Extracting ffmpeg...")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(BIN_DIR)
    os.remove(zip_path)

    for root, dirs, files in os.walk(BIN_DIR):
        if os.path.basename(root).lower() == "bin":
            for file in files:
                if file.endswith(".exe"):
                    src = os.path.join(root, file)
                    dest = os.path.join(BIN_DIR, file)
                    if src != dest:
                        shutil.move(src, dest)

    for item in os.listdir(BIN_DIR):
        path = os.path.join(BIN_DIR, item)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)

    return os.path.isfile(FFMPEG_PATH)

def get_ffmpeg_path():
    return FFMPEG_PATH if is_ffmpeg_downloaded() else None
