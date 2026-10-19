"""Start KoSa and open it in your browser:  python run.py"""

import os
import threading
import webbrowser

import uvicorn

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:8000")).start()
    uvicorn.run("server:app", port=8000)
