from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import sqlite3
import uvicorn
import csv
import io
import os
import datetime
import threading
import time
import requests
import subprocess
import hashlib
import hmac
import secrets

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "accounts.db"
BACKUP_DIR = "backups"

# ---------------- PIN HASHING ----------------
def hash_pin(pin: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), bytes.fromhex(salt), 200_000).hex()
    return f"pbkdf2${salt}${digest}"

def verify_pin_hash(pin: str, stored: str) -> bool:
    try:
        _, salt, digest = stored.split("$")
    except ValueError:
        return False
    candidate = hash_pin(pin, salt).split("$")[2]
    return hmac.compare_digest(candidate, digest)

def get_stored_pin() -> str:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='pin'")
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def init_db():
    print("Checking database...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Accounts table
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id TEXT,
        password TEXT,
        email TEXT,
        ban_start TEXT,
        duration_days INTEGER,
        notes TEXT
    )''')
    try:
        c.execute("ALTER TABLE accounts ADD COLUMN notes TEXT")
    except sqlite3.OperationalError:
        pass
        
    # Ban history: mga daan nga ban sa matag account
    c.execute('''CREATE TABLE IF NOT EXISTS ban_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_pk INTEGER,
        ban_start TEXT,
        duration_days INTEGER,
        archived_at TEXT
    )''')

    # Settings table para sa PIN
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    # PIN: i-hash na. Kung plaintext pa ang daan nga PIN, i-convert nato (parehas gihapon ang PIN).
    c.execute("SELECT value FROM settings WHERE key='pin'")
    row = c.fetchone()
    if row is None:
        c.execute("INSERT INTO settings (key, value) VALUES ('pin', ?)", (hash_pin('1234'),))
    elif not row[0].startswith("pbkdf2$"):
        c.execute("UPDATE settings SET value=? WHERE key='pin'", (hash_pin(row[0]),))
    
    conn.commit()
    conn.close()
    print("Database ready.")

def create_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(BACKUP_DIR, f"backup_{timestamp}.csv")
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT account_id, email, password, ban_start, duration_days, notes FROM accounts")
        rows = c.fetchall()
        if not rows:
            conn.close()
            return
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["account_id", "email", "password", "ban_start", "duration_days", "notes"])
            writer.writerows(rows)
        conn.close()
        print(f"✅ Auto-backup created: {filename}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")

def backup_worker():
    while True:
        time.sleep(3600)
        create_backup()

init_db()
create_backup()
threading.Thread(target=backup_worker, daemon=True).start()

class Account(BaseModel):
    account_id: str
    password: str
    email: str
    ban_start: str | None = None
    duration_days: int = 0
    notes: str | None = None

class SettingData(BaseModel):
    key: str
    value: str

class UpdateData(BaseModel):
    url: str

# ---------------- LOCK / SECURITY ----------------
PROTECTED_KEYS = {"pin"}              # dili pwede basahon o usbon pinaagi sa settings API
PUBLIC_API_PATHS = {"/api/verify-pin"}  # ang uban tanan kinahanglan naka-unlock
active_tokens = set()                 # naay token = naka-unlock ang app
pin_attempts = {"count": 0, "locked_until": 0.0}

class PinData(BaseModel):
    pin: str

class ChangePinData(BaseModel):
    current: str
    new: str

@app.middleware("http")
async def require_unlock(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path not in PUBLIC_API_PATHS and request.method != "OPTIONS":
        if request.headers.get("X-Auth-Token", "") not in active_tokens:
            return JSONResponse(status_code=401, content={"detail": "App is locked"})
    return await call_next(request)

@app.post("/api/verify-pin")
def verify_pin(data: PinData):
    now = time.time()
    if now < pin_attempts["locked_until"]:
        wait = int(pin_attempts["locked_until"] - now) + 1
        raise HTTPException(status_code=429, detail=f"Too many attempts. Try again in {wait}s.")
    if verify_pin_hash(data.pin, get_stored_pin()):
        pin_attempts["count"] = 0
        token = secrets.token_urlsafe(32)
        active_tokens.add(token)
        return {"status": "success", "token": token}
    pin_attempts["count"] += 1
    if pin_attempts["count"] >= 5:
        pin_attempts["count"] = 0
        pin_attempts["locked_until"] = now + 30
    raise HTTPException(status_code=401, detail="Incorrect PIN")

@app.post("/api/lock")
def lock_app(request: Request):
    active_tokens.discard(request.headers.get("X-Auth-Token", ""))
    return {"status": "locked"}

@app.post("/api/change-pin")
def change_pin(data: ChangePinData):
    if not verify_pin_hash(data.current, get_stored_pin()):
        raise HTTPException(status_code=401, detail="Incorrect current PIN")
    if not (data.new.isdigit() and len(data.new) == 4):
        raise HTTPException(status_code=400, detail="PIN must be exactly 4 digits")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('pin', ?)", (hash_pin(data.new),))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/accounts")
def get_accounts():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT accounts.*,
                 (SELECT COUNT(*) FROM ban_history h WHERE h.account_pk = accounts.id) AS history_count
                 FROM accounts ORDER BY id DESC""")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

@app.post("/api/accounts")
def add_account(acc: Account):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO accounts (account_id, password, email, ban_start, duration_days, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (acc.account_id, acc.password, acc.email, acc.ban_start, acc.duration_days, acc.notes))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.put("/api/accounts/{acc_id}")
def update_account(acc_id: int, acc: Account):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Kung nakabutang na'y ban ug gi-ilisan sa bag-ong Ban Start, i-save ang daan sa history
    c.execute("SELECT ban_start, duration_days FROM accounts WHERE id=?", (acc_id,))
    old = c.fetchone()
    archived = False
    if old and old[0] and (old[1] or 0) > 0 and acc.ban_start and acc.ban_start != old[0]:
        c.execute("INSERT INTO ban_history (account_pk, ban_start, duration_days, archived_at) VALUES (?, ?, ?, ?)",
                  (acc_id, old[0], old[1], datetime.datetime.now().isoformat(timespec="seconds")))
        archived = True
    c.execute('''UPDATE accounts SET account_id=?, password=?, email=?, ban_start=?, duration_days=?, notes=? WHERE id=?''',
              (acc.account_id, acc.password, acc.email, acc.ban_start, acc.duration_days, acc.notes, acc_id))
    conn.commit()
    conn.close()
    return {"status": "success", "archived": archived}

@app.delete("/api/accounts/{acc_id}")
def delete_account(acc_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM accounts WHERE id = ?", (acc_id,))
    c.execute("DELETE FROM ban_history WHERE account_pk = ?", (acc_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/accounts/{acc_id}/history")
def get_history(acc_id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, ban_start, duration_days, archived_at FROM ban_history WHERE account_pk = ? ORDER BY id DESC", (acc_id,))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

@app.delete("/api/history/{hist_id}")
def delete_history(hist_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM ban_history WHERE id = ?", (hist_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/import")
async def import_csv(file: UploadFile = File(...)):
    contents = await file.read()
    decoded = contents.decode('utf-8-sig') 
    reader = csv.DictReader(io.StringIO(decoded))
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    count = 0
    for row in reader:
        def get_val(possible_keys, default=''):
            for key in row.keys():
                if not key: continue
                clean_key = key.strip().lower().replace(' ', '_')
                for pk in possible_keys:
                    if clean_key == pk:
                        return row[key] if row[key] else default
            return default

        acc_id = get_val(['account_id', 'accountid', 'id', 'account'])
        email = get_val(['email', 'account_email', 'email_address'])
        password = get_val(['password', 'pass', 'email_password'])
        ban_start = get_val(['ban_start', 'ban_start_date_&_time', 'ban_start_date', 'start_date'], None)
        duration = get_val(['duration_days', 'ban_duration_(days)', 'ban_duration', 'duration', 'days'], '0')
        notes = get_val(['notes', 'note', 'recovery_email'], '')

        if not acc_id and not email: continue
        try:
            duration_int = int(float(duration)) if duration else 0
        except:
            duration_int = 0

        c.execute("INSERT INTO accounts (account_id, email, password, ban_start, duration_days, notes) VALUES (?, ?, ?, ?, ?, ?)",
                  (acc_id, email, password, ban_start, duration_int, notes))
        count += 1
    conn.commit()
    conn.close()
    create_backup() 
    return {"status": "success", "imported": count}

@app.get("/api/settings/{key}")
def get_setting(key: str):
    if key in PROTECTED_KEYS:
        raise HTTPException(status_code=403, detail="This setting is protected")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"key": key, "value": row[0]}
    raise HTTPException(status_code=404, detail="Setting not found")

@app.post("/api/settings")
def update_setting(data: SettingData):
    if data.key in PROTECTED_KEYS:
        raise HTTPException(status_code=403, detail="This setting is protected")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (data.key, data.value))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/update-app")
def update_app(data: UpdateData):
    download_url = data.url
    if not download_url:
        raise HTTPException(status_code=400, detail="No URL provided")
    
    try:
        new_exe_name = "CS2Tracker_update.exe"
        
        # Check kung HTML page ba ang gi-download imbes .exe file
        if download_url.endswith(".html") or ("github.com" in download_url and "releases/download" not in download_url):
            raise Exception("Invalid download link. Attach a .exe file to your GitHub Release.")

        # Gamita ang requests imbes urllib para smooth ang download
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        with open(new_exe_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Buhaton ang updater.bat script
        bat_script = """
        @echo off
        timeout /t 2 /nobreak >nul
        taskkill /f /im CS2Tracker.exe >nul 2>&1
        timeout /t 1 /nobreak >nul
        del CS2Tracker.exe >nul 2>&1
        ren CS2Tracker_update.exe CS2Tracker.exe
        start "" CS2Tracker.exe
        del "%~f0"
        """
        with open("updater.bat", "w") as f:
            f.write(bat_script)
            
        subprocess.Popen(["updater.bat"], shell=True)
        
        return {"status": "success", "message": "Update downloaded. Restarting..."}
    except Exception as e:
        print(f"Update Error: {str(e)}") 
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)