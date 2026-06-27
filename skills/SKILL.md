# Skill: NeverZero Platform Healing

## Overview

This skill enables an autonomous agent to monitor, diagnose, and heal a NeverZero real-time AI platform deployment using Gemini 3.5 Flash Computer Use.

## Prerequisites

- Python 3.10+
- `GOOGLE_API_KEY` environment variable
- Running NeverZero instance (local or remote)
- `NEVERZERO_BASE_URL` and `NEVERZERO_API_KEY` environment variables

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Start the Health Dashboard

```bash
python dashboard/health_dashboard.py
```

Serves at `http://localhost:8080`. This is what the agent screenshots and analyzes.

### 2. Run the Self-Healer (Simulation Mode)

```bash
SELF_HEALER_SIMULATE=true python agent/healer.py
```

Runs without Gemini API calls. Useful for testing the orchestration logic.

### 3. Run the Self-Healer (Live Mode)

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
export NEVERZERO_BASE_URL="http://localhost:3000"
export NEVERZERO_API_KEY="your-neverzero-api-key"
python agent/healer.py
```

## Architecture

```
┌─────────────────┐     screenshot      ┌──────────────────────────┐
│ Health Dashboard│ ─────────────────────▶│ Gemini 3.5 Flash         │
│  (localhost:8080)│                      │  Computer Use            │
└─────────────────┘                       │                          │
                                          │ 1. Analyze screenshot    │
                                          │ 2. Gather context        │
                                          │ 3. Reason about issues   │
                                          │ 4. Generate fix actions  │
                                          └──────────────────────────┘
                                                       │
                                                       ▼
                                          ┌──────────────────────────┐
                                          │ NeverZero API            │
                                          │  (fix auth, clear cache,  │
                                          │   trigger compaction)     │
                                          └──────────────────────────┘
```

## File Reference

| File | Purpose |
|------|---------|
| `agent/gemini_computer_use.py` | Gemini 3.5 Flash Computer Use API integration |
| `agent/neverzero_client.py` | NeverZero platform API client |
| `agent/healer.py` | Main orchestrator: observe → reason → act |
| `dashboard/health_dashboard.py` | Real-time metrics dashboard |
| `skills/AGENTS.md` | Agent persona and operational rules |
| `skills/SKILL.md` | This file — technical skill documentation |

## API Methods

### `GeminiComputerUseAgent.reason(screenshot_b64, context)`

Analyzes a dashboard screenshot and telemetry context. Returns a diagnosis string.

- If healthy: returns `HEALTHY`
- If issues found: returns `ALERT: [description]. SUGGESTED FIX: [action].`

### `NeverZeroClient`

| Method | Description |
|--------|-------------|
| `get_health()` | Fetch system health status |
| `get_recent_events(limit)` | Fetch recent events from ledger |
| `get_auth_stats()` | Fetch authentication statistics |
| `fix_auth_service_url(url)` | Update auth service URL |
| `clear_redis_cache(pattern)` | Clear Redis cache |
| `trigger_compaction(feature_id)` | Trigger feature compaction |

### `SelfHealer.run(cycles)`

Runs the monitoring loop. Set `cycles` to limit iterations (default: infinite).

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes (live) | — | Gemini API key |
| `NEVERZERO_BASE_URL` | No | `http://localhost:3000` | NeverZero API base URL |
| `NEVERZERO_API_KEY` | No | — | NeverZero API key |
| `SELF_HEALER_SIMULATE` | No | `false` | Run in simulation mode |
| `SELF_HEALER_POLL_INTERVAL` | No | `30` | Seconds between cycles |

## Troubleshooting

**Gemini API errors:** Verify `GOOGLE_API_KEY` is set and has access to `gemini-3.5-flash-preview-07-2026`.

**Dashboard not reachable:** Ensure `dashboard/health_dashboard.py` is running on port 8080.

**NeverZero API errors:** Verify `NEVERZERO_BASE_URL` and that the instance is running.

## Extending

To add new fix types:

1. Add detection logic in `SelfHealer.apply_fix()`
2. Add the corresponding API method in `NeverZeroClient`
3. Update `AGENTS.md` with the new capability

