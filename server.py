from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler
from subprocess import Popen, run
import os, time, pathlib, io, zipfile, urllib.request, sys

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT / "src"
BIN  = ROOT / "bin"
BIN.mkdir(exist_ok=True)

def ensure_ffmpeg() -> str:
    """Download a static ffmpeg binary into ./bin (once per container)."""
    ffmpeg_path = BIN / "ffmpeg"
    if ffmpeg_path.exists():
        return str(ffmpeg_path)

    url = ("https://github.com/icholy/ffmpeg-static/releases/latest/download/"
           "ffmpeg-amd64")          # ~10 MB, no archive, direct binary
    for attempt in range(3):
        try:
            print(f"↙  Downloading ffmpeg (try {attempt+1}/3)", file=sys.stderr)
            data = urllib.request.urlopen(url, timeout=180).read()
            ffmpeg_path.write_bytes(data)
            ffmpeg_path.chmod(0o755)
            print("✓  ffmpeg ready →", ffmpeg_path, file=sys.stderr)
            return str(ffmpeg_path)
        except Exception as e:
            print("⚠️  ffmpeg fetch failed:", e, file=sys.stderr)
            time.sleep(15)
    raise RuntimeError("Could not fetch ffmpeg")

FFMPEG = ensure_ffmpeg()
os.environ["PATH"] = f"{BIN}:{os.environ['PATH']}"   # make ffmpeg/rclone discoverable

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

RECORDINGS_DIR = SRC / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)   # <<< Method A

def run_recorder():
    Popen(
        ["python", "main.py", "-user", "gragalbert", "-mode", "automatic"],
        cwd=SRC
    )

def refresh_loop():
    while True:
        run(["python", ROOT / "refresh_cookie.py"])
        time.sleep(90 * 60)          # every 90 min

def upload_loop():
    while True:
        run([
            RCLONE, "move",
            str(RECORDINGS_DIR),
            "drive:pop4u/jcayne_",
            "--include", "*.mp4",
            "--transfers", "4",
            "--delete-empty-src-dirs"
        ])
        time.sleep(15 * 60)          # every 15 min

if __name__ == "__main__":
    Thread(target=refresh_loop, daemon=True).start()
    Thread(target=run_recorder,  daemon=True).start()
    Thread(target=upload_loop,   daemon=True).start()

    HTTPServer(("", int(os.getenv("PORT", 10000))),
               SimpleHTTPRequestHandler).serve_forever()
