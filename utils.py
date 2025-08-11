def get_styles():
    return """
    QWidget {
        background-color: #12121c;
        color: #d0d0e0;
        font-family: 'Segoe UI', sans-serif;
        font-size: 11pt;
    }
    QLabel {
        color: #9a79ff;
    }
    QLineEdit {
        background-color: #1c1c2e;
        color: white;
        border: 1px solid #9a79ff;
        padding: 6px;
        border-radius: 4px;
    }
    QPushButton {
        background-color: #3e0f75;
        color: white;
        padding: 6px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #5c19b2;
    }
    QTextEdit {
        background-color: #1c1c2e;
        color: white;
        border: 1px solid #9a79ff;
        padding: 6px;
        border-radius: 4px;
    }
    QProgressBar {
        background-color: #1c1c2e;
        color: white;
        border: 1px solid #9a79ff;
        border-radius: 4px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #5c19b2;
    }
    """


def get_tab_styles():
    return """
    QTabWidget::pane {
        border: 1px solid #9a79ff;
        background: #12121c;
    }
    QTabBar::tab {
        background: #1c1c2e;
        color: white;
        padding: 8px 16px;
        border: 1px solid #9a79ff;
    }
    QTabBar::tab:selected {
        background: #3e0f75;
    }
    """


def get_help_text():
    return """
How to get Spotify Client ID and Client Secret:
1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account.
3. Click "Create an App".
4. Give your app a name and description, accept terms.
5. After creation, click your app and copy:
   - Client ID
   - Client Secret
6. Paste these values in the Configuration tab.

How to download FFMPEG:
1. Visit https://ffmpeg.org/download.html
2. Download the static build for your OS.
3. Extract it to a known folder.
4. Inside 'bin', find ffmpeg.exe.

Adding FFMPEG to PATH (Windows):
1. Copy the path of the 'bin' folder (where ffmpeg.exe is located).
2. Press Win+R, type "sysdm.cpl", press Enter.
3. Go to "Advanced" → "Environment Variables".
4. Under "System variables", select "Path" and click "Edit".
5. Click "New" and paste the folder path.
6. Press OK, then restart any terminal or application.
    """
