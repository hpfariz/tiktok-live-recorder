from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler
from subprocess import Popen, run
import os, time, pathlib, io, zipfile, urllib.request, stat, sys

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT / "src"
RCLONE = ROOT / "bin" / "rclone"          
BIN  = ROOT / "bin"

BIN.mkdir(exist_ok=True)

def ensure_rclone() -> str:
    """Download the rclone binary into ./bin the first time the service starts."""
    rclone_path = BIN / "rclone"
    if rclone_path.exists():
        return str(rclone_path)

    urls = [
        # primary mirror — GitHub’s releases CDN
        "https://github.com/rclone/rclone/releases/latest/download/"
        "rclone-current-linux-amd64.zip",
        # fallback — rclone.org
        "https://downloads.rclone.org/rclone-current-linux-amd64.zip",
    ]
    for url in urls:
        for attempt in range(3):
            try:
                print(f"↙  Downloading rclone (try {attempt+1}/3) from", url,
                      file=sys.stderr)
                data = urllib.request.urlopen(url, timeout=120).read()
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    src = next(n for n in z.namelist() if n.endswith("/rclone"))
                    extracted = z.extract(src, BIN)
                    # move & chmod
                    final = rclone_path
                    pathlib.Path(extracted).rename(final)
                    final.chmod(0o755)
                    print("✓  rclone ready →", final, file=sys.stderr)
                    return str(final)
            except Exception as e:
                print("⚠️  rclone fetch failed:", e, file=sys.stderr)
                time.sleep(10)
    raise RuntimeError("Could not fetch rclone from any mirror")

RCLONE = ensure_rclone()                # ← executes once at startup

def run_recorder():
    # run FROM the src directory, no extra args needed
    Popen(
        ["python", "main.py", "-user", "ewc_en", "-mode", "automatic", "-proxy", os.getenv("HTTPS_PROXY")],
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
                RCLONE, "move",
                str(SRC / "recordings"),
                "drive:pop4u/jcayne_",
                "--include", "*.mp4",
                "--create-dirs",
                "--transfers", "4",
                "--delete-empty-src-dirs"
            ])
            time.sleep(15 * 60)
                   # every 15 min

    Thread(target=upload_loop, daemon=True).start()


    HTTPServer(("", int(os.getenv("PORT", 10000))),
               SimpleHTTPRequestHandler).serve_forever()
