from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler
from subprocess import Popen, run
import os, time, pathlib, io, zipfile, urllib.request, sys, shutil

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT / "src"
BIN  = ROOT / "bin"
BIN.mkdir(exist_ok=True)

# --------------------------------------------------------------------------- #
# 1.  One-time rclone downloader (unchanged except for the single direct URL)
# --------------------------------------------------------------------------- #
def ensure_rclone() -> str:
    rclone_path = BIN / "rclone"
    if rclone_path.exists():
        return str(rclone_path)

    url = "https://downloads.rclone.org/v1.70.3/rclone-v1.70.3-linux-amd64.zip"
    for attempt in range(3):
        try:
            print(f"↙  Downloading rclone (try {attempt+1}/3)", file=sys.stderr)
            data = urllib.request.urlopen(url, timeout=180).read()
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                src = next(n for n in z.namelist() if n.endswith("/rclone"))
                extracted = z.extract(src, BIN)
                pathlib.Path(extracted).rename(rclone_path)
                rclone_path.chmod(0o755)
                print("✓  rclone ready →", rclone_path, file=sys.stderr)
                return str(rclone_path)
        except Exception as e:
            print("⚠️  rclone fetch failed:", e, file=sys.stderr)
            time.sleep(15)
    raise RuntimeError("Could not fetch rclone")

RCLONE = ensure_rclone()

# --------------------------------------------------------------------------- #
# 2.  One-time ffmpeg installer (runtime apt-get, no external URL)
# --------------------------------------------------------------------------- #
def ensure_ffmpeg() -> str:
    if shutil.which("ffmpeg"):
        return "ffmpeg"                             # already on PATH

    print("↙  Installing ffmpeg via apt-get", file=sys.stderr)
    try:
        run(["apt-get", "update", "-qq"], check=True)
        run(["apt-get", "install", "-yqq", "ffmpeg"], check=True)
        print("✓  ffmpeg ready → /usr/bin/ffmpeg", file=sys.stderr)
        return "ffmpeg"
    except Exception as e:
        raise RuntimeError(f"Could not install ffmpeg: {e}")

FFMPEG = ensure_ffmpeg()                            # executes once

# --------------------------------------------------------------------------- #
# 3.  Make sure the recordings directory exists (Method A)
# --------------------------------------------------------------------------- #
RECORDINGS_DIR = SRC / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# 4.  Threads
# --------------------------------------------------------------------------- #
def run_recorder():
    Popen(
        [
            "python", "main.py",
            "-user", "thewintersmolder",
            "-mode", "automatic",
            "-output", "recordings"
        ],
        cwd=SRC
    )

def refresh_loop():
    while True:
        run(["python", ROOT / "refresh_cookie.py"])
        time.sleep(90 * 60)

def upload_loop():
    while True:
        run([
            RCLONE, "move",
            str(RECORDINGS_DIR),
            "drive:pop4u/jcayne_",
            "--include", "*_final.mp4",
            "--transfers", "4",
            "--delete-empty-src-dirs"
        ])
        time.sleep(15 * 60)

# --------------------------------------------------------------------------- #
# 5.  Kick everything off
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    Thread(target=refresh_loop, daemon=True).start()
    Thread(target=run_recorder,  daemon=True).start()
    Thread(target=upload_loop,   daemon=True).start()

    HTTPServer(("", int(os.getenv("PORT", 10000))),
               SimpleHTTPRequestHandler).serve_forever()
