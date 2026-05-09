"""
QR Attendance System — Local Backend Server
============================================
Serves scanner.html and proxies scan requests to Google Apps Script.
The secret token lives here only — never exposed to the browser.

Setup:
  pip3 install requests

Run (two terminals):
  Terminal 1: python3 server.py
  Terminal 2: sudo tailscale serve --bg http://localhost:8080

Staff scanner URL (via Tailscale):
  https://<your-device>.tail<id>.ts.net/scanner.html
"""

import http.server
import urllib.parse
import requests
import json
import os

# ── CONFIGURATION ───────────────────────────────────────────
# Copy these from your deployed Google Apps Script
GOOGLE_APPS_SCRIPT_URL = "YOUR_APPS_SCRIPT_WEB_APP_URL_HERE"

# Generate a strong token:  openssl rand -hex 32
# Paste the same token in your Apps Script (see apps_script.js)
SECRET_TOKEN = "YOUR_SECRET_TOKEN_HERE"
# ────────────────────────────────────────────────────────────

HOST = "127.0.0.1"   # local only — Tailscale handles external HTTPS
PORT = 8080
DIR  = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # ── /scan endpoint ─────────────────────────────────────
        # Browser sends: student ID, name, type, time, device
        # Server adds:   secret token
        # Google receives full request — token never in browser
        if parsed.path == "/scan":
            params = urllib.parse.parse_qs(parsed.query)

            id_   = params.get("id",     [""])[0]
            name  = params.get("name",   [""])[0]
            type_ = params.get("type",   [""])[0]
            time_ = params.get("time",   [""])[0]
            dev   = params.get("device", ["Unknown"])[0]

            if not all([id_, name, type_, time_]):
                self._respond(400, {"status": "missing_params"})
                return

            try:
                resp = requests.get(GOOGLE_APPS_SCRIPT_URL, params={
                    "id":     id_,
                    "name":   name,
                    "type":   type_,
                    "time":   time_,
                    "device": dev,
                    "token":  SECRET_TOKEN,
                }, timeout=10)
                data = resp.json()
            except Exception as e:
                data = {"status": "server_error", "detail": str(e)}

            self._respond(200, data)
            return

        # ── Static file serving ────────────────────────────────
        super().do_GET()

    def _respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


if __name__ == "__main__":
    if "YOUR_APPS_SCRIPT" in GOOGLE_APPS_SCRIPT_URL:
        print("⚠️  WARNING: Please set GOOGLE_APPS_SCRIPT_URL and SECRET_TOKEN before running.")
        exit(1)

    print(f"""
╔══════════════════════════════════════════════════╗
║   QR Attendance Server                           ║
║   Local:  http://127.0.0.1:{PORT}/scanner.html   ║
║   HTTPS via Tailscale Serve                      ║
╚══════════════════════════════════════════════════╝
Press Ctrl+C to stop.
""")
    server = http.server.HTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
