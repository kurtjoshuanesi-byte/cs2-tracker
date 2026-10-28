import threading
import time
import uvicorn
import webview
import sys
import os
import pystray
from PIL import Image
import ctypes
import multiprocessing

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def on_minimize():
    window.hide()
    tray_icon.visible = True

def on_closing():
    window.hide()
    tray_icon.visible = True
    return False 

def on_show(icon, item):
    icon.visible = False
    window.restore() 
    window.show()    

def on_quit(icon, item):
    icon.stop()
    window.destroy()
    os._exit(0) 

if __name__ == '__main__':
    # 1. SINGLE INSTANCE LOCK (Para dili mo-doble ang app ug tray icon)
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\CS2TrackerMutex")
    if ctypes.windll.kernel32.GetLastError() == 183: # 183 means "Already Exists"
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
    
    global tray_icon
    tray_icon = pystray.Icon('CS2Tracker', image, 'CS2 Account Tracker', menu)
    
    threading.Thread(target=tray_icon.run, daemon=True).start()

    # 6. I-connect ang Events
    window.events.minimized += on_minimize
    window.events.closing += on_closing 

    # 7. Start Webview
    webview.start()