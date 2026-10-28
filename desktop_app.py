import threading
import time
import uvicorn
import webview
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(1.5)

    # Pangitaa ang icon path
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(application_path, 'app.ico')

    window = webview.create_window(
        title='CS2 Account Tracker', 
        url='http://127.0.0.1:8000', 
        width=1280, 
        height=800,
        background_color='#0f172a',
        icon=icon_path  # <--- Gidugang ang icon diri
    )
    
    webview.start()