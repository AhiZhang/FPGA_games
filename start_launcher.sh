#!/bin/bash
LOG=/tmp/fpga_games.log
KEEPLOG=/home/xilinx/fpga_games/fpga_games.log
PIDFILE=/tmp/fpga_games.pid
APP=/home/xilinx/fpga_games/launcher.py

if [ "$(id -u)" -ne 0 ]; then
  echo "start_launcher.sh must run as root" >&2
  exit 1
fi

set -a
if [ -f /etc/environment ]; then
  . /etc/environment
fi
set +a
for f in /etc/profile.d/*.sh; do
  [ -r "$f" ] && . "$f"
done
export XILINX_XRT="${XILINX_XRT:-/usr}"
export PATH="/usr/local/share/pynq-venv/bin:${PATH}"
PY=/usr/local/share/pynq-venv/bin/python3

log() {
  echo "$*" | tee -a "$LOG" >> "$KEEPLOG"
}

log "==== $(date -Iseconds) start_launcher ===="
log "XILINX_XRT=$XILINX_XRT PY=$PY"

for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if pgrep -f /boot/boot.py >/dev/null 2>&1; then
    log "waiting for /boot/boot.py to finish ($i)"
    sleep 3
  else
    break
  fi
done

log "stopping jupyter and leftover HDMI users"
systemctl stop jupyter >>"$LOG" 2>&1 || true
systemctl stop jupyter-notebook >>"$LOG" 2>&1 || true
pkill -f jupyter || true
pkill -f recognize.py || true
pkill -f clock_hdmi.py || true

if [ -f "$PIDFILE" ]; then
  old=$(cat "$PIDFILE" || true)
  if [ -n "${old:-}" ] && kill -0 "$old" 2>/dev/null; then
    kill "$old" 2>/dev/null || true
    sleep 1
    kill -9 "$old" 2>/dev/null || true
  fi
fi
if [ -f /tmp/snake.pid ]; then
  old=$(cat /tmp/snake.pid || true)
  if [ -n "${old:-}" ] && kill -0 "$old" 2>/dev/null; then
    kill "$old" 2>/dev/null || true
  fi
fi
pkill -f /home/xilinx/fpga_games/launcher.py || true
pkill -f /home/xilinx/fpga_games/snake.py || true
sleep 3
sync

log "==== $(date -Iseconds) launching menu download=${FPGA_DOWNLOAD:-${SNAKE_DOWNLOAD:-0}} ===="
setsid nohup env \
  XILINX_XRT="$XILINX_XRT" \
  PATH="$PATH" \
  FPGA_DOWNLOAD="${FPGA_DOWNLOAD:-${SNAKE_DOWNLOAD:-0}}" \
  "$PY" -u "$APP" >> "$LOG" 2>&1 < /dev/null &
echo $! > "$PIDFILE"
setsid nohup tail -n 0 -F "$LOG" >> "$KEEPLOG" 2>/dev/null < /dev/null &
chmod 644 "$LOG" "$PIDFILE" "$KEEPLOG" 2>/dev/null || true
log "launched pid=$(cat "$PIDFILE") XILINX_XRT=$XILINX_XRT"
