#!/usr/bin/env bash
# ============================================================
#  up.sh — Start Ollama + OpenViking stack (Linux/macOS)
#
#  Prerequisites:
#    - Ollama installed (https://ollama.com)
#    - OpenViking installed (pip install openviking)
#    - nomic-embed-text model pulled (ollama pull nomic-embed-text)
#    - Config files in ~/.openviking/
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OV_CONF="${OPENVIKING_CONFIG_FILE:-$HOME/.openviking/ov.conf}"
OV_LOG="$HOME/.openviking/server.log"
OV_PID="$HOME/.openviking/server.pid"

echo "=== Starting OpenViking Stack ==="

# --- Start Ollama ---
echo "[1/3] Starting Ollama..."
if curl -s http://localhost:11434/ >/dev/null 2>&1; then
    echo "      Ollama already running."
else
    ollama serve &>/dev/null &
    echo "      Waiting for Ollama..."
    for i in $(seq 1 30); do
        if curl -s http://localhost:11434/ >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    if curl -s http://localhost:11434/ >/dev/null 2>&1; then
        echo "      Ollama is ready."
    else
        echo "      ERROR: Ollama failed to start after 30s."
    fi
fi

# --- Start OpenViking server ---
echo "[2/3] Starting OpenViking server..."
if curl -s http://localhost:1933/health >/dev/null 2>&1; then
    echo "      OpenViking already running."
else
    OPENVIKING_CONFIG_FILE="$OV_CONF" \
        nohup openviking-server --config "$OV_CONF" --port 1933 \
        > "$OV_LOG" 2>&1 &
    echo $! > "$OV_PID"

    echo "      Waiting for OpenViking..."
    for i in $(seq 1 30); do
        if curl -s http://localhost:1933/health >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done
    if curl -s http://localhost:1933/health >/dev/null 2>&1; then
        echo "      OpenViking is ready."
    else
        echo "      ERROR: OpenViking failed to start after 60s."
        echo "      Check $OV_LOG"
    fi
fi

# --- Set Ollama to low priority after model load ---
echo "[3/3] Setting Ollama to low priority..."
curl -s -X POST http://localhost:11434/v1/embeddings \
    -H "Content-Type: application/json" \
    -d '{"model":"nomic-embed-text","input":"warmup"}' >/dev/null 2>&1
sleep 2
pgrep -f "ollama" | while read pid; do
    renice 19 -p "$pid" >/dev/null 2>&1 || true
done
echo "      Ollama priority set to nice 19."

echo ""
echo "=== Stack is UP ==="
echo "  Ollama:     http://localhost:11434"
echo "  OpenViking: http://localhost:1933"
echo "  Logs:       $OV_LOG"
