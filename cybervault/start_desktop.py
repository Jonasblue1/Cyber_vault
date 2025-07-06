"""
CyberVault Standalone Desktop Launcher
Starts the backend server and opens a PyWebView desktop window to http://localhost:8080
"""
import subprocess
import sys
import time
import threading
import webview
import os

BACKEND_PATH = os.path.join('backend', 'app.py')

# Start backend server in a background thread
def start_backend():
    subprocess.Popen([sys.executable, BACKEND_PATH])
    # Wait for server to start
    time.sleep(2)

if __name__ == '__main__':
    threading.Thread(target=start_backend, daemon=True).start()
    # Open PyWebView window
    webview.create_window('CyberVault', 'http://localhost:8080', width=1024, height=768)
    webview.start()
