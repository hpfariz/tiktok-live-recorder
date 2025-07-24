# refresh_cookie.py – overwrites src/cookies.json with a fresh ttwid
import httpx, json, pathlib, sys

TARGET = "https://www.tiktok.com/@tiktok"          # any public page
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; "
      "rv:126.0) Gecko/20100101 Firefox/126.0")

with httpx.Client(headers={"User-Agent": UA}, follow_redirects=True) as c:
    c.get(TARGET, timeout=10)
    if "ttwid" not in c.cookies:
        print("❌  No ttwid cookie received", file=sys.stderr)
        sys.exit(1)

cookie_path = pathlib.Path(__file__).parent / "src" / "cookies.json"
cookie_path.write_text(json.dumps({"ttwid": c.cookies["ttwid"]}))
print("Refreshed   ttwid  →", cookie_path)