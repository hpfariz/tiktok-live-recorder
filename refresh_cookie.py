# refresh_cookie.py  – grabs a new anonymous 'ttwid' cookie
import httpx, pathlib, sys

# 1. GET any TikTok page (anonymous visit)
TARGET = "https://www.tiktok.com/@tiktok"   # any public URL works
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) "
      "Gecko/20100101 Firefox/126.0")

with httpx.Client(follow_redirects=True, headers={"User-Agent": UA}) as c:
    c.get(TARGET, timeout=10)
    # 2. Pull the 'ttwid' cookie TikTok sets on first redirect
    if "ttwid" not in c.cookies:
        print("No ttwid cookie received", file=sys.stderr)
        sys.exit(1)

    t = c.cookies.get("ttwid")
    netscape = (
        "# Netscape HTTP Cookie File\n"
        # domain,  includeSub  path  secure  expiry  name   value
        f".tiktok.com\tTRUE\t/\tTRUE\t0\tttwid\t{t}\n"
    )

# 3. Overwrite cookies.txt in the repo root
ck_path = pathlib.Path(__file__).with_name("cookies.txt")
ck_path.write_text(netscape)
print("Refreshed ttwid →", ck_path)
