#!/bin/bash
# ============================================================
# QR Attendance System — Watchdog Script
# Runs every minute via crontab
# Checks: internet, Tailscale, Tailscale Serve, Python server
# Auto-restarts anything that's broken
#
# Crontab entry:
#   * * * * * bash /path/to/watchdog.sh
# ============================================================

LOG="/path/to/tamkeen/watchdog.log"           # update this path
PYTHON_SCRIPT="/path/to/server.py"            # update this path
PYTHON_WORKDIR="/path/to/server/directory"    # update this path

log() {
    echo "[$(date '+%d/%m/%Y %H:%M:%S')] $1" >> "$LOG"
}

# ── 1. Internet check ─────────────────────────────────────────
if ! ping -c 2 -W 3 8.8.8.8 &>/dev/null; then
    log "❌ Internet unreachable — restarting NetworkManager"
    sudo systemctl restart NetworkManager
    sleep 15
    if ! ping -c 2 8.8.8.8 &>/dev/null; then
        log "❌ Internet still down after restart"
    else
        log "✅ Internet restored"
    fi
else
    log "✅ Internet OK"
fi

# ── 2. Tailscale check ────────────────────────────────────────
TS_STATUS=$(sudo tailscale status 2>&1)

if echo "$TS_STATUS" | grep -q "Tailscale is stopped\|not running"; then
    log "❌ Tailscale down — restarting"
    sudo systemctl restart tailscaled
    sleep 5
    sudo tailscale up 2>/dev/null || true
    sleep 5
    sudo tailscale serve --bg http://localhost:8080 2>/dev/null || true
    log "✅ Tailscale restarted"
elif ! sudo tailscale serve status 2>/dev/null | grep -q "proxy http://localhost:8080"; then
    log "⚠️ Tailscale Serve not running — restarting serve"
    sudo tailscale serve --bg http://localhost:8080 2>/dev/null || true
    log "✅ Tailscale Serve restarted"
else
    log "✅ Tailscale OK"
fi

# ── 3. Python server check ────────────────────────────────────
if ! pgrep -f "server.py" > /dev/null; then
    log "❌ Python server not running — restarting"
    cd "$PYTHON_WORKDIR"
    nohup python3 "$PYTHON_SCRIPT" >> "$LOG" 2>&1 &
    log "✅ Python server restarted (PID: $!)"
else
    log "✅ Python server OK"
fi

# ── 4. HTTP endpoint check ────────────────────────────────────
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/scanner.html 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    log "✅ Scanner endpoint OK"
else
    log "⚠️ Scanner endpoint returned HTTP $HTTP_CODE"
fi

# ── Keep log small (last 500 lines) ──────────────────────────
tail -500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
