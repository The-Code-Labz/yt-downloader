#!/usr/bin/env python3
"""Pull fresh YouTube cookies straight from a real, already-logged-in browser
on this machine and push them to the deployed backend's /admin/cookies
endpoint — so the worker's yt-dlp session stays authenticated without ever
manually re-exporting a cookies.txt.

Meant to run on the machine (or network) where you actually watch YouTube —
that session already has good standing with YouTube, unlike a bare cloud/VPS
IP. Schedule it (cron / systemd timer / Task Scheduler) every 15-60 minutes;
each run overwrites the previous cookies with the latest session state.

Requires: pip install -r scripts/requirements.txt
Requires: the target browser closed, OR run on a platform where
browser_cookie3 can read the SQLite cookie DB while the browser is open
(it copies the file first — works on Linux/macOS; Chrome on Windows may
briefly fail if the DB is locked, in which case the script just skips that
run and tries again next schedule).

Usage:
    python refresh_cookies.py \\
        --browser chrome \\
        --backend-url https://api-yt-downloader.neurolearninglabs.com \\
        --admin-secret "$ADMIN_SECRET"

Or via env vars (handy for cron so the secret isn't in the crontab in plaintext):
    REFRESH_COOKIES_BROWSER=chrome
    REFRESH_COOKIES_BACKEND_URL=https://api-yt-downloader.neurolearninglabs.com
    REFRESH_COOKIES_ADMIN_SECRET=...
"""
from __future__ import annotations

import argparse
import http.cookiejar
import os
import sys
import tempfile
import urllib.error
import urllib.request

try:
    import browser_cookie3
except ImportError:
    print("Missing dependency. Run: pip install -r scripts/requirements.txt", file=sys.stderr)
    sys.exit(1)

SUPPORTED_BROWSERS = (
    "chrome", "chromium", "brave", "edge", "firefox", "opera", "opera_gx", "vivaldi", "safari",
)


def extract_cookies(browser: str) -> http.cookiejar.CookieJar:
    fn = getattr(browser_cookie3, browser, None)
    if fn is None:
        raise SystemExit(f"Unsupported browser '{browser}'. Choose from: {', '.join(SUPPORTED_BROWSERS)}")
    # domain_name is a substring match — this pulls every cookie whose domain
    # contains "youtube.com", i.e. youtube.com + .youtube.com, which is what
    # yt-dlp actually needs (the same set a "Get cookies.txt" export would give).
    return fn(domain_name="youtube.com")


def to_netscape_bytes(cj: http.cookiejar.CookieJar) -> bytes:
    """Serialize a CookieJar to Netscape cookies.txt format in-memory."""
    mjar = http.cookiejar.MozillaCookieJar()
    for cookie in cj:
        mjar.set_cookie(cookie)
    with tempfile.NamedTemporaryFile(mode="r", suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        mjar.save(tmp_path, ignore_discard=True, ignore_expires=True)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


def push(backend_url: str, admin_secret: str, payload: bytes) -> None:
    url = backend_url.rstrip("/") + "/admin/cookies"
    req = urllib.request.Request(
        url,
        data=payload,
        method="PUT",
        headers={"X-Admin-Secret": admin_secret, "Content-Type": "text/plain"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"OK {resp.status} — pushed {len(payload)} bytes to {url}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Push failed: HTTP {exc.code} — {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Push failed: {exc.reason}") from exc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--browser", default=os.environ.get("REFRESH_COOKIES_BROWSER", "chrome"),
                     choices=SUPPORTED_BROWSERS)
    ap.add_argument("--backend-url", default=os.environ.get("REFRESH_COOKIES_BACKEND_URL"),
                     help="e.g. https://api-yt-downloader.neurolearninglabs.com")
    ap.add_argument("--admin-secret", default=os.environ.get("REFRESH_COOKIES_ADMIN_SECRET"))
    ap.add_argument("--save-local", metavar="PATH",
                     help="Also write the Netscape cookies.txt to a local path (optional, for debugging)")
    args = ap.parse_args()

    if not args.backend_url or not args.admin_secret:
        ap.error("--backend-url and --admin-secret are required (or set the REFRESH_COOKIES_* env vars)")

    try:
        cj = extract_cookies(args.browser)
    except Exception as exc:  # noqa: BLE001 — browser_cookie3 raises varied errors per-OS/browser
        raise SystemExit(f"Could not read cookies from {args.browser}: {exc}") from exc

    cookies = list(cj)
    if not cookies:
        raise SystemExit(
            f"No youtube.com cookies found in {args.browser} — are you logged into "
            "youtube.com in that browser on this machine?"
        )
    payload = to_netscape_bytes(cj)
    print(f"Extracted {len(cookies)} cookies from {args.browser}")

    if args.save_local:
        with open(args.save_local, "wb") as f:
            f.write(payload)
        print(f"Saved local copy: {args.save_local}")

    push(args.backend_url, args.admin_secret, payload)


if __name__ == "__main__":
    main()
