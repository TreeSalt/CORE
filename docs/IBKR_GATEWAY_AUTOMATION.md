# IBKR Gateway Automation & Recovery Guide

## Mission
Ensure institutional-grade, hands-free automation for spinning up the IB Gateway and pulling data/executing, while maintaining absolute strictness on failing closed and leaking zero credentials.

## Overview
The `ibkr_gateway_supervisor.sh` script handles process orchestration for IBKR. It avoids storing plain-text credentials by launching the headless (or GUI) Gateway process and requiring the user to perform the manual 2FA/login step **once**, then programmatically waits for the API port (`4002`) to accept connections securely.

## Quick Start (Commands)

```bash
# 1. Start the gateway (if not already running)
make ibkr-up

# 2. Wait for the API to come online (fails closed if timeout hits)
make ibkr-wait

# 3. Probe the API manually to see verbose errors if offline
make ibkr-probe

# 4. Complete Data Pipeline (Start -> Wait -> Ingest 30d of MES 5m)
make ibkr-ingest-30d
```

## First-Time UI Setup (TWS / IB Gateway)
1. Open IB Gateway or TWS.
2. Go to **Settings > API > Settings**.
3. **Enable** "Enable ActiveX and Socket Clients".
4. **Disable** "Read-Only API" (if you intend to trade).
5. Set **Socket port** to `4002` (Paper) or `4001` (Live). 
   *(Note: The `Makefile` uses `4002` as the default paper port).*
6. **Apply and Restart**.

## Troubleshooting Matrix

| Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| `FAIL-CLOSED: Gateway binary not found` | `IBGATEWAY_BIN` path is incorrect. | Ensure the binary exists at `/home/AWS/.local/opt/ibgateway/ibgateway` or override `IBGATEWAY_BIN` env var. |
| `Timeout reached. Gateway did not open port 4002.` | Gateway is hung at login, 2FA prompt, or wrong port in settings. | Check the GUI, complete login, verify API settings port is `4002`. |
| `API connection failed: ConnectionRefusedError` | Gateway is up, but API box is unchecked in settings. | Enable "ActiveX and Socket Clients" in Gateway API settings. |

## Strict Zero-Secret Policy
There are **no** `user` or `password` parameters accepted by these scripts. Authentication is decoupled from technical API readiness by design to meet the institutional fail-closed mandate.
