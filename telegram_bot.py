#!/usr/bin/env python3
"""
QR Attendance System — Telegram Monitor Bot
============================================
Remotely monitor and control your attendance server via Telegram.

Commands:
  /status  — check if everything is running
  /log     — show last 20 lines of watchdog log
  /restart — restart the Python server
  /reboot  — reboot the Raspberry Pi

Setup:
  1. Create a bot via @BotFather in Telegram → get BOT_TOKEN
  2. Get your chat ID via @userinfobot in Telegram
  3. Fill in the config below
  4. Run: python3 telegram_bot.py &

Install:
  pip3 install requests
"""

import os
import subprocess
import time
import requests

# ── CONFIGURATION ────────────────────────────────────────────
BOT_TOKEN   = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # from @BotFather
CHAT_ID     = "YOUR_TELEGRAM_CHAT_ID_HERE"    # from @userinfobot
LOG_FILE    = "/path/to/tamkeen/watchdog.log" # update this path
SERVER_FILE = "/path/to/server.py"            # update this path
SERVER_DIR  = "/path/to/server/directory"     # update this path
# ─────────────────────────────────────────────────────────────

BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send(text):
    try:
        requests.post(f"{BASE}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")


def get_status():
    lines = ["<b>🖥 SERVER STATUS</b>\n"]

    r = subprocess.run(["ping", "-c", "1", "-W", "3", "8.8.8.8"], capture_output=True)
    lines.append("✅ Internet — OK" if r.returncode == 0 else "❌ Internet — DOWN")

    r = subprocess.run(["sudo", "tailscale", "status"], capture_output=True, text=True)
    lines.append("✅ Tailscale — Connected" if "100." in r.stdout else "❌ Tailscale — Disconnected")

    r = subprocess.run(["sudo", "tailscale", "serve", "status"], capture_output=True, text=True)
    lines.append("✅ Tailscale Serve — Running" if "proxy" in r.stdout else "⚠️ Tailscale Serve — Not running")

    r = subprocess.run(["pgrep", "-f", "server.py"], capture_output=True)
    lines.append("✅ Python Server — Running" if r.returncode == 0 else "❌ Python Server — Stopped")

    try:
        r = requests.get("http://127.0.0.1:8080/scanner.html", timeout=5)
        lines.append(f"✅ Scanner URL — HTTP {r.status_code}")
    except:
        lines.append("❌ Scanner URL — Unreachable")

    lines.append(f"\n🕐 <i>{time.strftime('%d/%m/%Y %H:%M:%S')}</i>")
    return "\n".join(lines)


def get_log():
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        last = lines[-20:] if len(lines) >= 20 else lines
        return "<b>📋 Last 20 log lines:</b>\n\n<code>" + "".join(last) + "</code>"
    except:
        return "❌ Log file not found"


def restart_server():
    subprocess.run(["pkill", "-f", "server.py"])
    time.sleep(2)
    subprocess.Popen(["python3", SERVER_FILE], cwd=SERVER_DIR,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "✅ Python server restarted"


def reboot_pi():
    send("⚠️ Rebooting in 5 seconds...")
    time.sleep(5)
    subprocess.run(["sudo", "reboot"])


def handle(update):
    msg  = update.get("message", {})
    text = msg.get("text", "").strip().lower()
    chat = str(msg.get("chat", {}).get("id", ""))

    if chat != CHAT_ID:
        return  # ignore messages from other users

    if text in ["/start", "/help"]:
        send("<b>🤖 Attendance Monitor Bot</b>\n\n"
             "/status — Server health check\n"
             "/log — Last 20 watchdog log lines\n"
             "/restart — Restart Python server\n"
             "/reboot — Reboot the Pi")
    elif text == "/status":
        send(get_status())
    elif text == "/log":
        send(get_log())
    elif text == "/restart":
        send("🔄 Restarting server...")
        send(restart_server())
    elif text == "/reboot":
        reboot_pi()


def main():
    if "YOUR_TELEGRAM" in BOT_TOKEN:
        print("⚠️ Please set BOT_TOKEN and CHAT_ID before running.")
        exit(1)

    send("🟢 <b>Attendance Monitor Bot started</b>\nSend /help for commands.")
    offset = None

    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{BASE}/getUpdates", params=params, timeout=35)
            for update in r.json().get("result", []):
                handle(update)
                offset = update["update_id"] + 1
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
