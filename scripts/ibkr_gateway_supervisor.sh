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
# Support positional args or flags
if [ "$ACTION" == "up" ] || [ "$ACTION" == "wait" ] || [ "$ACTION" == "probe" ]; then
    PORT="${3:-4002}"
    TIMEOUT="${5:-90}"
else
    # Fallback if no flags are passed just the action
    PORT="4002"
    TIMEOUT="90"
fi

IBGATEWAY_BIN="${IBGATEWAY_BIN:-/home/AWS/.local/opt/ibgateway/ibgateway}"

function check_api_ready() {
    local p="$1"
    python3 scripts/ibkr_api_probe.py --port "$p" >/dev/null 2>&1
}

function run_probe() {
    # Visible probe execution for the user
    python3 scripts/ibkr_api_probe.py --port "$PORT" || exit 1
}

function run_up() {
    echo "🔌 Orchestrating IB Gateway Startup (Target Port: $PORT)..."
    if check_api_ready "$PORT"; then
        echo "✅ API Port $PORT is already open and responsive. Gateway is considered active and logged in."
        return 0
    fi
    
    if pgrep -f "ibgateway" >/dev/null 2>&1 || pgrep -f "tws" >/dev/null 2>&1; then
        echo "⚠️  Gateway/TWS process detected, but API $PORT is unresponsive."
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
    
    echo "⏳ Gateway launched; please complete login/2FA; waiting for API $PORT..."
}

function run_wait() {
    echo "⏳ Waiting up to ${TIMEOUT}s for API Port $PORT to open and become responsive..."
    start_time=$(date +%s)
    
    while true; do
        if check_api_ready "$PORT"; then
            echo "✅ SUCCESS: API Port $PORT is now OPEN and accepting connections."
            exit 0
        fi
        
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        
        if [ "$elapsed" -ge "$TIMEOUT" ]; then
            echo "❌ FAIL-CLOSED: Timeout (${TIMEOUT}s) reached."
            echo "   Gateway API did not become responsive on port $PORT."
            echo "   It may be hung at login/2FA, configuration is wrong, or another process is blocking."
            echo "   Run 'make ibkr-probe' to see the exact connection error."
            exit 1
        fi
        
        sleep 2
    done
}

function usage() {
    echo "Usage: $0 {up|wait|probe} [--port PORT] [--timeout SECONDS]"
    echo "Commands:"
    echo "  up    - Start gateway if absent. Reports if manual login is needed."
    echo "  wait  - Wait for the API port to open and evaluate readiness (default 4002, timeout 90s)"
    echo "  probe - Execute a single API readiness probe with visible output"
    exit 1
}

case "$ACTION" in
    up)
        run_up
        ;;
    wait)
        run_wait
        ;;
    probe)
        run_probe
        ;;
    *)
        usage
        ;;
esac
