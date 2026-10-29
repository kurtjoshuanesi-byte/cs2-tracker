# CS2 Account Tracker

A local-first desktop/web app for tracking CS2 G2G account bans and cooldowns. Keep your accounts organized and never miss a cooldown expiration again.

![CS2 Tracker Preview](app.ico)

## Features
- **PIN Lock Security:** Protects your database with a 4-digit PIN. Includes a manual lock button.
- **Smart Notifications:** Get Windows popups and audio alerts 1 day, 2 hours, and 10 minutes before a ban expires, plus an alert exactly when it's ready.
- **Quiet Hours (DND):** Set a time range to mute notifications so you aren't disturbed while sleeping or working.
- **Real-time countdowns:** Tracks exactly when a ban expires down to the second.
- **Filter tabs & Auto-sort:** Quickly view All, Banned, or Ready accounts, with the closest to expiring always at the top.
- **System Tray Integration:** Minimize to the system tray to keep your taskbar clean. Double-click the tray icon to restore.
- **Auto-Updater:** In-app update checker and downloader. It downloads the new version, replaces the old `.exe`, and restarts automatically.
- **CSV Import/Export:** Easily move your data from Excel or Google Sheets.
- **Auto-backup:** Automatically saves a `.csv` backup every hour to the `backups/` folder.
- **Native Desktop App:** Runs as a standalone `.exe` with a custom icon using PyWebView.

## Requirements
- Python 3.10 or higher
- Windows OS (for the desktop app, system tray, and notifications)

## Setup & Installation

1. **Clone the repository:**
   ```
   git clone https://github.com/kurtjoshuanesi-byte/cs2-tracker.git
   cd cs2-tracker

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Run the Web Version:**

```bash
python main.py
```

4. **Open your browser and go to http://127.0.0.1:8000**

Run the Desktop App:

```bash
python desktop_app.py
```

5. **Building the Standalone .exe**

If you want to compile this into a single executable file with the custom icon:

```bash
pip install pyinstaller
py -m PyInstaller --noconsole --onefile --clean --name "CS2Tracker" --icon="app.ico" --add-data "index.html;." --add-data "app.ico;." desktop_app.py
```

Note: Move the CS2Tracker.exe from the dist/ folder back to the main folder so it can find the database and backups.

***Security & Disclaimer***

This tool is strictly for personal tracking only.
Do not upload your accounts.db or backup files to public repositories. The .gitignore is already configured to prevent this. Use this software at your own risk.


### Unsaon pag-push sa GitHub:

Sa imong terminal (siguroa nga naa ka sa `cs2-tracker` folder), i-type ni:

```bash
git add README.md
git commit -m "Update README with latest features and instructions"
git push origin main
```




