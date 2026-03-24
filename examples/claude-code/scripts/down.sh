#!/usr/bin/env bash
# ============================================================
#  down.sh — Stop Ollama + OpenViking stack (Linux/macOS)
# ============================================================

set -euo pipefail

OV_PID_FILE="$HOME/.openviking/server.pid"

echo "=== Stopping OpenViking Stack ==="

# --- Stop OpenViking server ---
echo "[1/2] Stopping OpenViking..."
if [ -f "$OV_PID_FILE" ]; then
    OV_PID=$(cat "$OV_PID_FILE")
    if kill -0 "$OV_PID" 2>/dev/null; then
        kill "$OV_PID" 2>/dev/null || true
        sleep 1
        # Force kill if still alive
        kill -9 "$OV_PID" 2>/dev/null || true
    fi
    rm -f "$OV_PID_FILE"
fi
# Also kill by name as fallback
pkill -f "openviking-server" 2>/dev/null || true

if curl -s http://localhost:1933/health >/dev/null 2>&1; then
    echo "      WARNING: OpenViking still running!"
else
    echo "      OpenViking stopped."
fi

# --- Stop Ollama ---
echo "[2/2] Stopping Ollama..."
pkill -f "ollama serve" 2>/dev/null || true
sleep 1

if curl -s http://localhost:11434/ >/dev/null 2>&1; then
    echo "      WARNING: Ollama still running!"
else
    echo "      Ollama stopped."
fi

echo ""
echo "=== Stack is DOWN ==="
