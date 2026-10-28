import threading
import time
import uvicorn
import webview
import sys
import os
import pystray
from PIL import Image

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

# --- TRAY & WINDOW LOGIC ---
def on_minimize():
    # Itago ang window gikan sa taskbar
    window.hide()
    tray_icon.visible = True

def on_closing():
    # Kung i-click ang X button, i-hide ang window imbes nga isira ang app
    window.hide()
    tray_icon.visible = True
    return False # Kini nga 'False' maoy mopugong sa pag-close sa app

def on_show(icon, item):
    # Itago ang tray icon ug ipakita ang window
    icon.visible = False
    window.restore() # Ibalik gikan sa minimized/hidden state
    window.show()    # Ipakita sa front

def on_quit(icon, item):
    # Patyon ang tray ug ang app
    icon.stop()
    window.destroy()

if __name__ == '__main__':
    # 1. Start Server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    # 2. Setup Window
    window = webview.create_window(
        title='CS2 Account Tracker', 
        url='http://127.0.0.1:8000', 
        width=1280, 
        height=800,
        background_color='#0f172a'
    )

    # 3. Setup System Tray Icon
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

    # 4. I-connect ang Events
    window.events.minimized += on_minimize
    window.events.closing += on_closing # Nakig-intercept sa X button

    # 5. Start Webview
    webview.start()