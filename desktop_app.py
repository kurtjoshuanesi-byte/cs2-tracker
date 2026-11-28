import threading
import time
import json
import sqlite3
import datetime
import uvicorn
import webview
import sys
import os
import pystray
from PIL import Image
import ctypes
import multiprocessing

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app, DB_FILE

# Globals nga gikinahanglan sa tray notification worker
window = None
tray_icon = None
state = {"hidden": False}   # True kung naka-minimize na sa tray


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")


def set_hidden(value):
    state["hidden"] = value
    # Pabilin nga visible ang tray icon para mo-work ang notify()
    if tray_icon is not None:
        try:
            tray_icon.visible = True
        except Exception:
            pass


def on_minimize():
    window.hide()
    set_hidden(True)


def on_closing():
    window.hide()
    set_hidden(True)
    return False


def on_show(icon, item):
    window.restore()
    window.show()
    set_hidden(False)


def on_quit(icon, item):
    icon.stop()
    window.destroy()
    os._exit(0)


def notify(title, message):
    """Native Windows notification via system tray."""
    if tray_icon is None:
        return
    try:
        tray_icon.notify(message, title)
    except Exception as e:
        print("Notification failed:", e)


# ---------------- NOTIFICATION WORKER ----------------
def _load_settings(conn):
    try:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}


def _parse_hhmm(text, fallback):
    try:
        h, m = text.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return fallback


def _in_dnd(settings):
    if settings.get("dnd_enabled") != "true":
        return False
    now = datetime.datetime.now()
    current = now.hour * 60 + now.minute
    start = _parse_hhmm(settings.get("dnd_start", "22:00"), 22 * 60)
    end = _parse_hhmm(settings.get("dnd_end", "07:00"), 7 * 60)
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def _expiry_ms(row):
    """Kun ma-expire (ms) ang ban, o None kung walay valid ban."""
    ban_start, duration = row[2], row[3] or 0
    if not ban_start or duration <= 0:
        return None
    try:
        start = datetime.datetime.fromisoformat(str(ban_start))
    except ValueError:
        return None
    return start.timestamp() * 1000 + duration * 86_400_000


def _thresholds(diff):
    """I-return ang list sa (type, label, message) nga dapat ma-fire karon."""
    hits = []
    if 7_200_000 < diff <= 86_400_000:
        hits.append(("1d", "1 Day", "ready in 1 day"))
    if 600_000 < diff <= 7_200_000:
        hits.append(("2h", "2 Hours", "ready in 2 hours"))
    if 0 < diff <= 600_000:
        hits.append(("10m", "10 Minutes", "ready in 10 minutes"))
    if diff <= 0:
        hits.append(("ready", "Ready Now", "is now ready to play"))
    return hits


def notification_worker():
    seeded = False
    while True:
        try:
            conn = sqlite3.connect(DB_FILE)
            settings = _load_settings(conn)
            rows = conn.execute(
                "SELECT id, account_id, ban_start, duration_days FROM accounts"
            ).fetchall()

            try:
                sent = set(json.loads(settings.get("sent_alerts") or "[]"))
            except Exception:
                sent = set()

            now_ms = time.time() * 1000
            changed = False
            dnd = _in_dnd(settings)

            for row in rows:
                exp_ms = _expiry_ms(row)
                if exp_ms is None:
                    continue
                diff = exp_ms - now_ms
                for typ, label, message in _thresholds(diff):
                    key = "%s|%s|%d" % (typ, row[0], int(exp_ms))
                    if key in sent:
                        continue
                    # Seed lang sa unang dagan: markahi nga "sent" para
                    # dili mo-spam ang tanang daan nga account.
                    if not seeded or dnd or not state["hidden"]:
                        sent.add(key)
                        changed = True
                        continue
                    notify("CS2 Alert: " + label,
                           "Account %s %s" % (row[1], message))
                    sent.add(key)
                    changed = True

            if changed:
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES ('sent_alerts', ?)",
                    (json.dumps(sorted(sent)),),
                )
                conn.commit()

            conn.close()
            seeded = True
        except Exception as e:
            print("Notification worker error:", e)
        time.sleep(30)


if __name__ == '__main__':
    # 1. SINGLE INSTANCE LOCK (Para dili mo-doble ang app ug tray icon)
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\CS2TrackerMutex")
    if ctypes.windll.kernel32.GetLastError() == 183:  # 183 means "Already Exists"
        ctypes.windll.user32.MessageBoxW(0, "CS2 Tracker is already running in the system tray.", "App Running", 1)
        sys.exit(0)

    # 2. Freeze support para sa PyInstaller
    multiprocessing.freeze_support()

    # 3. Start Server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    # 4. Setup Window
    window = webview.create_window(
        title='CS2 Account Tracker',
        url='http://127.0.0.1:8000',
        width=1280,
        height=800,
        background_color='#0f172a'
    )

    # 5. Setup System Tray Icon
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(application_path, 'app.ico')
    image = Image.open(icon_path)

    menu = pystray.Menu(
        pystray.MenuItem('Show App', on_show, default=True),
        pystray.MenuItem('Quit', on_quit)
    )

    tray_icon = pystray.Icon('CS2Tracker', image, 'CS2 Account Tracker', menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

    # 6. Start notification worker (naa na ang tray_icon dinhi)
    threading.Thread(target=notification_worker, daemon=True).start()

    # 7. I-connect ang Events
    window.events.minimized += on_minimize
    window.events.closing += on_closing

    # 8. Start Webview
    webview.start()
