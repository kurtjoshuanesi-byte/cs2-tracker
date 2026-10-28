from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import uvicorn
import csv
import io
import os
import datetime
import threading
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "accounts.db"
BACKUP_DIR = "backups"

def init_db():
    print("Checking database...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
    conn.commit()
    conn.close()
    print("Database ready.")

# --- AUTO BACKUP ENGINE ---
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
            return # Ayaw og backup kung walay data
            
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["account_id", "email", "password", "ban_start", "duration_days", "notes"])
            writer.writerows(rows)
        conn.close()
        print(f"✅ Auto-backup created: {filename}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")

def backup_worker():
    # Mag-backup kada 1 ka oras (3600 seconds)
    while True:
        time.sleep(3600)
        create_backup()

# I-run ang startup backup ug i-start ang background thread
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

@app.get("/api/accounts")
def get_accounts():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM accounts ORDER BY id DESC")
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
    c.execute('''UPDATE accounts SET account_id=?, password=?, email=?, ban_start=?, duration_days=?, notes=? WHERE id=?''',
              (acc.account_id, acc.password, acc.email, acc.ban_start, acc.duration_days, acc.notes, acc_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/accounts/{acc_id}")
def delete_account(acc_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM accounts WHERE id = ?", (acc_id,))
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

        if not acc_id and not email:
            continue

        try:
            duration_int = int(float(duration)) if duration else 0
        except:
            duration_int = 0

        c.execute("INSERT INTO accounts (account_id, email, password, ban_start, duration_days, notes) VALUES (?, ?, ?, ?, ?, ?)",
                  (acc_id, email, password, ban_start, duration_int, notes))
        count += 1
        
    conn.commit()
    conn.close()
    
    # Mag-backup dayon human sa import
    create_backup() 
    
    return {"status": "success", "imported": count}

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)