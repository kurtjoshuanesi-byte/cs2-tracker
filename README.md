<p align="center">

<img width="4000" height="2250" alt="Untitled design (1)-1" src="https://github.com/user-attachments/assets/4059eeb9-0882-4283-b069-c442158d298c" />
<img width="4000" height="2250" alt="Untitled design-1" src="https://github.com/user-attachments/assets/673cfe7b-7b3f-4f42-ab25-9e1b2f4b2046" />

</p>

# CS2 Account Tracker

A local-first desktop/web app for tracking CS2 G2G account bans and cooldowns. Keep your accounts organized and never miss a cooldown expiration again.

![CS2 Tracker Preview](app.ico)

## Features
- **PIN Lock Security:** Protects your data with a 4-digit PIN. The PIN is stored as a salted hash and checked by the server, and the API stays locked until the correct PIN is entered. 5 wrong attempts trigger a 30-second lockout. Includes a manual lock button.
- **Smart Notifications:** Get Windows popups and audio alerts 1 day, 2 hours, and 10 minutes before a ban expires, plus an alert exactly when it's ready. Alert history is saved, so you won't get the same alert twice after restarting the app.
- **Quiet Hours (DND):** Set a time range to mute notifications so you aren't disturbed while sleeping or working.
- **Real-time countdowns:** Tracks exactly when a ban expires down to the second.
- **Ban History:** When you set a new Ban Start on an account that already has a ban, the old ban is saved automatically. Open it with the **History** button on each row. Entries can be removed.
- **Bulk Select & Delete:** Tick the checkboxes (or the header checkbox for everything currently visible) and delete many accounts at once. A backup is created before deleting.
- **Filter tabs & Auto-sort:** Quickly view All, Banned, or Ready accounts, with the closest to expiring always at the top.
- **Compact layout:** The table fits the window without side scrolling. Long values are shortened with "..." and show in full when you hover.
- **System Tray Integration:** Minimize to the system tray to keep your taskbar clean. Double-click the tray icon to restore.
- **Auto-Updater:** In-app update checker and downloader. It downloads the new version, replaces the old `.exe`, and restarts automatically.
- **CSV Import/Export:** Easily move your data from Excel or Google Sheets.
- **Auto-backup:** Automatically saves a `.csv` backup every hour (and before every bulk delete) to the `backups/` folder.
- **Native Desktop App:** Runs as a standalone `.exe` with a custom icon using PyWebView.

## Requirements
- Python 3.10 or higher
- Windows OS (for the desktop app, system tray, and notifications)

## Setup & Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/kurtjoshuanesi-byte/cs2-tracker.git
   cd cs2-tracker
   ```

2. **Install dependencies:**

   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Run the Web Version:**

   ```bash
   python main.py
   ```

   Open your browser and go to http://127.0.0.1:8000

4. **Run the Desktop App:**

   ```bash
   python desktop_app.py
   ```

The default PIN on first run is `1234`. Change it in **Settings** right away.

## Notes
- Notifications are only checked while the app is **unlocked**. If the app is locked, no alerts are fired.
- The server only listens on `127.0.0.1`, so it is not reachable from other devices on your network.

## Building the Standalone .exe

If you want to compile this into a single executable file with the custom icon:

```bash
pip install pyinstaller
py -m PyInstaller --noconsole --onefile --clean --name "CS2Tracker" --icon="app.ico" --add-data "index.html;." --add-data "app.ico;." desktop_app.py
```

Note: Move the `CS2Tracker.exe` from the `dist/` folder back to the main folder so it can find the database and backups.

## Releasing an Update

1. Bump `CURRENT_VERSION` in `index.html` (for example `1.5.0`).
2. Build the new `CS2Tracker.exe` (see above).
3. On GitHub, create a new Release with a tag that matches the version (for example `v1.5.0`).
4. Attach `CS2Tracker.exe` as the release file (it should be the only attached file). The in-app updater downloads the first attached file.

## What's New in v1.5.0
- PIN is now stored as a salted hash and verified by the server; the API is locked until the PIN is entered, with a 30-second lockout after 5 wrong attempts.
- The server now listens on `127.0.0.1` only.
- Alert history is saved, so alerts no longer repeat every time the app is opened.
- Fixed the update check so versions such as `1.10.0` are correctly seen as newer than `1.4.0`.
- New: Ban History per account.
- New: Bulk select and delete.
- New: Table layout that fits the window without side scrolling.

## Security & Disclaimer

This tool is strictly for personal tracking only.

- Account passwords and backup CSV files are stored as plain text on your own PC. Keep the folder private.
- Do not upload your `accounts.db` or backup files to public repositories. The `.gitignore` is already configured to prevent this.
- Use this software at your own risk.
