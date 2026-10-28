# CS2 Account Tracker

A local-first desktop/web app for tracking CS2 G2G account bans and cooldowns. Keep your accounts organized and never miss a cooldown expiration again.

## Features
- **Real-time countdowns:** Tracks exactly when a ban expires.
- **10-minute notifications:** Get a Windows popup alert 10 minutes before an account is ready to play.
- **Filter tabs:** Quickly view All, Banned, or Ready accounts.
- **Auto-sort:** The account closest to expiring is always at the top.
- **CSV Import/Export:** Easily move your data from Excel or Google Sheets.
- **Auto-backup:** Automatically saves a `.csv` backup every hour to the `backups/` folder.
- **Native Desktop App:** Runs as a standalone `.exe` using PyWebView (no browser address bar).

## Requirements
- Python 3.10 or higher
- Windows OS (for the desktop app and notifications)

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kurtjoshuanesi-byte/cs2-tracker.git
   cd cs2-tracker
