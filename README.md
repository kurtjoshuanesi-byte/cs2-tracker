# CS2 Account Tracker

A local-first desktop/web app for tracking CS2 G2G account bans and cooldowns.

## Features
- Real-time countdowns for ban expiration.
- 10-minute Windows notifications before cooldown expires.
- Filter tabs (All, Banned, Ready).
- Auto-sort by nearest expiration.
- CSV Import/Export.
- Auto-backup (every hour).
- Native Desktop App using PyWebView.

## Requirements
- Python 3.10+
- FastAPI, Uvicorn, PyWebView

## Setup
1. Install dependencies:
   ```bash
   pip install fastapi uvicorn pywebview
