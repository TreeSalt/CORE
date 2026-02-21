#!/usr/bin/env bash
# scripts/ibkr_gateway_supervisor.sh
# ==============================================================================
# Fail-closed, institutional-grade IB Gateway Orchestrator.
# Ensures the Gateway is running and waits for the API port to become available.
# Will NEVER print secrets or credentials to logs.

set -e
set -u
set -o pipefail

ACTION="${1:-}"
PORT_FLAG="${2:-}"
PORT="${3:-4002}"
TIMEOUT_FLAG="${4:-}"
TIMEOUT="${5:-90}"

IBGATEWAY_BIN="${IBGATEWAY_BIN:-/home/AWS/.local/opt/ibgateway/ibgateway}"

function check_port_open() {
    # Check if a TCP port is listening on 127.0.0.1
    local p="$1"
    (echo > /dev/tcp/127.0.0.1/"$p") >/dev/null 2>&1
}

function run_up() {
    echo "🔌 Orchestrating IB Gateway Startup (Target Port: $PORT)..."
    if check_port_open "$PORT"; then
        echo "✅ API Port $PORT is already open. Gateway is considered active and logged in."
        return 0
    fi
    
    if pgrep -f "ibgateway" >/dev/null 2>&1 || pgrep -f "tws" >/dev/null 2>&1; then
        echo "⚠️  Gateway/TWS process detected, but port $PORT is CLOSED."
        echo "   Gateway launched; please complete login/2FA; waiting for port $PORT..."
        return 0
    fi

    if [ ! -f "$IBGATEWAY_BIN" ] && [ ! -x "$IBGATEWAY_BIN" ]; then
        echo "❌ FAIL-CLOSED: Gateway binary not found at $IBGATEWAY_BIN"
        echo "   Cannot auto-start. Please launch TWS/Gateway manually and login."
        exit 1
    fi

    echo "🚀 Launching IB Gateway via $IBGATEWAY_BIN..."
    "$IBGATEWAY_BIN" >/dev/null 2>&1 &
    
    echo "⏳ Gateway launched; please complete login/2FA; waiting for port $PORT..."
}

function run_wait() {
    echo "⏳ Waiting up to ${TIMEOUT}s for API Port $PORT to open..."
    start_time=$(date +%s)
    
    while true; do
        if check_port_open "$PORT"; then
            echo "✅ SUCCESS: API Port $PORT is now OPEN and accepting connections."
            exit 0
        fi
        
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        
        if [ "$elapsed" -ge "$TIMEOUT" ]; then
            echo "❌ FAIL-CLOSED: Timeout (${TIMEOUT}s) reached."
            echo "   Gateway did not open port $PORT. It may be hung at login/2FA, or configuration is wrong."
            exit 1
        fi
        
        sleep 2
    done
}

function usage() {
    echo "Usage: $0 {up|wait} [--port PORT] [--timeout SECONDS]"
    echo "Commands:"
    echo "  up    - Start gateway if absent. Reports if manual login is needed."
    echo "  wait  - Wait for the API port to open (default 4002, timeout 90s)"
    exit 1
}

case "$ACTION" in
    up)
        run_up
        ;;
    wait)
        run_wait
        ;;
    *)
        usage
        ;;
esac
