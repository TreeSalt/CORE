---
DOMAIN: 03_ORCHESTRATION
MODEL: qwen3.5:9b
TIER: cruiser
TYPE: ARCHITECTURE
STATUS: PENDING_REVIEW
---

# ARCHITECTURE: SOVEREIGN DASHBOARD

## Overview

This single-page HTML dashboard provides real-time visibility into the sovereign mission control interface without requiring any build step or backend server. It renders live data from the vault ledger and maintains operational awareness through automatic refresh cycles.

---

## JSON Data Sources

### Required Files (fetch() URLs)

1. **`/api/vault/ledger/current.json`**
   - Current epoch timestamp
   - Chain integrity status
   - Last write timestamp
   - Health metrics

2. **`/api/vault/mission/queue.json`**
   - Mission queue state
   - Active mission IDs
   - Pending actions count

3. **`/api/vault/rationification/requests.json`**
   - Ratification requests list
   - Request timestamps
   - Current status flags
   - Escalation thresholds

4. **`/api/vault/escalations/recent.json`**
   - Recent escalation events
   - Event severity levels
   - Resolution status
   - Escalation reasons

5. **`/api/vault/ledger/entries/recent.json`**
   - Latest ledger entries
   - Entry IDs
   - Transaction hashes
   - Entry timestamps

6. **`/api/vault/snapshot/latest.json`**
   - Trust class summary
   - Snapshot metadata
   - Protocol version
   - Authority status

---

## HTML Structure (Mockup)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sovereign Dashboard</title>
    <style>
        :root {
            --primary: #3b82f6;
            --danger: #ef4444;
            --success: #22c55e;
            --warning: #eab308;
            --neutral: #6b7280;
            --bg-dark: #111827;
            --panel: #1f2937;
            --border: #374151;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: var(--bg-dark);
            color: #e5e7eb;
            min-height: 100vh;
        }

        .dashboard {
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
        }

        .epoch-badge {
            background: var(--primary);
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: bold;
        }

        .refresh-indicator {
            color: var(--neutral);
            font-size: 0.875rem;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }

        .panel {
            background: var(--panel);
            border-radius: 8px;
            padding: 1.5rem;
            border: 1px solid var(--border);
        }

        .panel h3 {
            margin-bottom: 1rem;
            color: #9ca3af;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .status-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
        }

        .status-icon {
            width: 24px;
            height: 24px;
            border-radius: 4px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
        }

        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .success { background: rgba(34, 197, 94, 0.2); color: var(--success); }
        .danger { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
        .warning { background: rgba(234, 179, 8, 0.2); color: var(--warning); }

        .actions {
            display: flex;
            gap: 0.5rem;
        }

        button {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
            transition: opacity 0.2s;
        }

        button:hover { opacity: 0.9; }

        .btn-approve { background: var(--success); color: white; }
        .btn-reject { background: var(--danger); color: white; }

        .entry-item {
            font-size: 0.875rem;
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
        }

        .entry-hash {
            font-family: monospace;
            color: var(--neutral);
            word-break: break-all;
        }

        @media (max-width: 768px) {
            header { flex-direction: column; gap: 1rem; align-items: flex-start; }
            .actions { width: 100%; }
            button { flex: 1; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <header>
            <div>
                <h1 style="margin-bottom: 0.25rem;">SOVEREIGN DASHBOARD</h1>
                <p style="color: var(--neutral); font-size: 0.875rem;">Vault Mission Control Interface</p>
            </div>
            <div style="text-align: right;">
                <div class="epoch-badge">Epoch #<span id="epoch"></span></div>
                <div class="refresh-indicator" id="last-updated"></div>
            </div>
        </header>

        <div class="grid">
            <!-- Vault Health Panel -->
            <section class="panel" style="grid-column: span 1;">
                <h3>Vault Health</h3>
                <div class="status-row">
                    <span>Last Write:</span>
                    <span id="last-write"></span>
                </div>
                <div class="status-row">
                    <span>Chain Integrity:</span helspan>
                    <span id="chain-status" class="status-badge"></span>
                </div>
                <div class="status-row">
                    <span>Trust Class:</span>
                    <span id="trust-class" class="status-badge"></span>
                </div>
                <div class="status-row">
                    <span>Status:</span>
                    <span id="authority-status" class="status-badge"></span>
                </div>
            </section>

            <!-- Mission Queue Panel -->
            <section class="panel">
                <h3>Mission Queue</h3>
                <div id="mission-queue-content">
                    <!-- Dynamically populated -->
                </div>
            </section>

            <!-- Ratification Panel -->
            <section class="panel" style="grid-column: span 2;">
                <h3>Ratification Queue</h3>
                <div id="ratification-queue-content">
                    <!-- Dynamically populated -->
                </div>
            </section>

            <!-- Escalations Panel -->
            <section class="panel">
                <h3>Recent Escalations</h3>
                <div id="escalation-list" style="font-size: 0.875rem;">
                    <!-- Dynamically populated -->
                </div>
            </section>

            <!-- Ledger Entries Panel -->
            <section class="panel" style="grid-column: span 1;">
                <h3>Recent Ledger Entries</h3>
                <div id="ledger-entries">
                    <!-- Dynamically populated -->
                </div>
            </section>
        </div>
    </div>

    <script>
        // Dashboard State Management
        const state = {
            interval: null,
            refreshRate: 30000, // 30 seconds
            apiBase: '/api/vault'
        };

        // Fetch and render data
        async function loadDashboard() {
            try {
                const [ledger, queue, ratification, escalations, entries, snapshot] = await Promise.all([
                    fetch(`${state.apiBase}/ledger/current.json`).then(r => r.json()),
                    fetch(`${state.apiBase}/mission/queue.json`).then(r => r.json()),
                    fetch(`${state.apiBase}/rationification/requests.json`).then(r => r.json()),
                    fetch(`${state.apiBase}/escalations/recent.json`).then(r => r.json()),
                    fetch(`${state.apiBase}/ledger/entries/recent.json`).then(r => r.json()),
                    fetch(`${state.apiBase}/snapshot/latest.json`).then(r => r.json())
                ]);

                renderDashboard(ledger, queue, ratification, escalations, entries, snapshot);
                updateTimestamp();
            } catch (error) {
                console.error('Failed to load dashboard:', error);
                document.getElementById('last-updated').textContent = 
                    '⚠️ Last refresh: Failed';
            }
        }

        // Render all sections
        function renderDashboard(ledger, queue, ratification, escalations, entries, snapshot) {
            // Epoch display
            document.getElementById('epoch').textContent = ledger.epoch;

            // Vault health
            const now = new Date(ledger.lastWrite).toLocaleTimeString();
            document.getElementById('last-write').textContent = now;
            
            const integrityEl = document.getElementById('chain-status');
            integrityEl.textContent = ledger.chainIntegrity ? '✓ Valid' : '✗ Compromised';
            integrityEl.className = `status-badge ${ledger.chainIntegrity ? 'success' : 'danger'}`;

            document.getElementById('trust-class').textContent = snapshot.trustClass || 'Unknown';
            document.getElementById('trust-class').className = `status-badge trust-${snapshot.trustClass?.toLowerCase()}`;

            const authorityEl = document.getElementById('authority-status');
            authorityEl.textContent = snapshot.authorityStatus || 'Offline';
            authorityEl.className = `status-badge ${snapshot.authorityStatus === 'active' ? 'success' : 
                                            snapshot.authorityStatus === 'pending' ? 'warning' : 'danger'}`;

            // Mission queue
            const queueContainer = document.getElementById('mission-queue-content');
            if (queue.items && queue.items.length > 0) {
                queueContainer.innerHTML = queue.items.slice(0, 5).map((item, i) => `
                    <div class="status-row">
                        <span>#[${item.id || i + 1}] ${item.name || item.task}</span>
                        <span class="status-badge ${getStatusClass(item.status)}">${item.status}</span>
                    </div>
                `).join('');
            } else {
                queueContainer.innerHTML = '<p style="color: var(--neutral); font-size: 0.8rem;">No active missions</p>';
            }

            // Ratification queue
            const ratContainer = document.getElementById('ratification-queue-content');
            if (ratification.requests && ratification.requests.length > 0) {
                ratContainer.innerHTML = ratification.requests.map(req => `
                    <div style="display: grid; grid-template-columns: 1fr auto; gap: 0.5rem; align-items: center;">
                        <div style="font-size: 0.875rem;">
                            ${req.id || req.hash} <span style="color: var(--neutral);">·</span> 
                            ${req.type || 'Ratification'} · ${req.description || ''}
                        </div>
                        <div class="actions">
                            <button class="btn-approve" data-id="${req.id}">Approve</button>
                            <button class="btn-reject" data-id="${req.id}">Reject</button>
                        </div>
                    </div>
                `).join('');

                ratContainer.querySelectorAll('.btn-approve').forEach(btn => {
                    btn.addEventListener('click', (e) => handleAction(e.target, 'approve'));
                });
                ratContainer.querySelectorAll('.btn-reject').forEach(btn => {
                    btn.addEventListener('click', (e) => handleAction(e.target, 'reject'));
                });
            } else {
                ratContainer.innerHTML = '<p style="color: var(--neutral); font-size: 0.8rem;">No pending ratifications</p>';
            }

            // Escalations
            const escContainer = document.getElementById('escalation-list');
            if (escalations.items && escalations.items.length > 0) {
                escContainer.innerHTML = escalations.items.slice(0, 5).map(evt => `
                    <div class="entry-item" style="border-left: 3px solid var(--danger)">
                        <strong>⚠️ Escalation:</strong> ${evt.reason || evt.message || 'Unknown'}
                        <div class="entry-hash">${evt.id || ''}</div>
                        <div style="color: var(--neutral); font-size: 0.75rem;">${evt.timestamp || ''}</div>
                    </div>
                `).join('');
            } else {
                escContainer.innerHTML = '<p style="color: var(--neutral); font-size: