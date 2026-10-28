import threading
import time
import uvicorn
import webview
import sys
import os

# Siguroa nga makit-an ang main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app

def run_server():
    # Nagdagan sa background, walay logs nga mopakita sa terminal
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

if __name__ == '__main__':
    # 1. I-start ang server sa background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # 2. Huwata og gamay para mo-boot ang server
    time.sleep(1.5)

    # 3. Buhaton ang Desktop Window
    window = webview.create_window(
        title='CS2 Account Tracker', 
        url='http://127.0.0.1:8000', 
        width=1280, 
        height=800,
        background_color='#0f172a' # Dark mode background
    )
    
    # 4. I-run ang app (Kini ang mo-block sa script hangtod isira ang window)
    webview.start()