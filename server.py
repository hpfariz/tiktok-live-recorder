from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler
from subprocess import Popen, run
import os, time, pathlib

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT / "src"

def run_recorder():
    Popen([
        "python", SRC / "main.py",
        "-user", "ewc_en", "-mode", "automatic",
        "-cookies", SRC / "cookies.json"          # <— here
    ])

def refresh_loop():
    while True:
        run(["python", ROOT / "refresh_cookie.py"])
        time.sleep(90 * 60)                      # every 90 min

if __name__ == "__main__":
    Thread(target=refresh_loop, daemon=True).start()
    Thread(target=run_recorder,  daemon=True).start()
    HTTPServer(("", int(os.getenv("PORT", 10000))),
               SimpleHTTPRequestHandler).serve_forever()
