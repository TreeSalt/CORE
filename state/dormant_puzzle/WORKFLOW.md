# JANE STREET DORMANT PUZZLE — CORE Workflow
## Deadline: April 1, 2026 (17 days)

### The Loop (repeat daily):

```
STEP 1: Factory generates probe hypotheses
  python3 scripts/orchestrator_loop.py
  → Produces probe files in state/dormant_puzzle/

STEP 2: You execute probes in Colab
  - Open https://colab.research.google.com/drive/1rIDPs1CtyRe9aISbwZkHLaYWxqVbOjdm
  - Upload PROBES_ROUND_N.json
  - Copy-paste scripts/colab_probe_runner.py into a cell
  - Change MODEL = "dormant-model-X" for each model
  - Run → download RESULTS file

STEP 3: Copy results back to CORE
  cp ~/Downloads/RESULTS_*.json state/dormant_puzzle/

STEP 4: Analyze locally
  .venv/bin/python3 scripts/analyze_dormant_results.py

STEP 5: Rate anomalies (human judgment)
  - Open RESULTS files
  - Set anomaly_score 0-10 for suspicious responses
  - Note any behavioral changes

STEP 6: Factory generates next round based on findings
  python3 scripts/orchestrator_loop.py
  → Reads ANALYSIS_LATEST.json
  → Generates PROBES_ROUND_N+1.json with targeted follow-ups
  → Repeat from STEP 2
```

### Rate Limit Strategy:
- ~30 probes per model per day (estimate)
- 3 models = ~90 total probes per day
- 17 days = ~1500 total probes
- Round 1 (today): 30 baseline + trigger probes per model
- Round 2+: Targeted based on Round 1 anomalies

### Key Files:
- state/dormant_puzzle/PROBES_ROUND_N.json — probes to execute
- state/dormant_puzzle/RESULTS_ROUND_N_MODEL_X.json — raw results
- state/dormant_puzzle/ANALYSIS_LATEST.json — automated analysis
- scripts/colab_probe_runner.py — copy into Colab
- scripts/analyze_dormant_results.py — local analysis
