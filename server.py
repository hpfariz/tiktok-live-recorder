from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler
from subprocess import Popen, run
import os, time, pathlib

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT / "src"

def run_recorder():
    # run FROM the src directory, no extra args needed
    Popen(
        ["python", "main.py", "-user", "jcayne_", "-mode", "automatic"],
        cwd=SRC                       # ← this makes cwd = src/
    )

def refresh_loop():
    while True:
        run(["python", ROOT / "refresh_cookie.py"])
        time.sleep(90 * 60)           # refresh every 90 min

if __name__ == "__main__":
    Thread(target=refresh_loop, daemon=True).start()
    Thread(target=run_recorder,  daemon=True).start()

    def upload_loop():
        while True:
            run([
                "rclone", "move",
                str(SRC / "recordings"),            # local source
                "drive:pop4u/jcayne_",              # ← desired Drive path
                "--include", "*.mp4",
                "--create-dirs",                    # makes pop4u/jcayne_ if missing
                "--transfers", "4",
                "--delete-empty-src-dirs",
                "--bwlimit", "15M"
            ])
            time.sleep(15 * 60)                    # every 15 min

    Thread(target=upload_loop, daemon=True).start()


    HTTPServer(("", int(os.getenv("PORT", 10000))),
               SimpleHTTPRequestHandler).serve_forever()
