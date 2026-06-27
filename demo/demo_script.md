# Demo Script — 1 Minute Video

## Setup (before recording)

```bash
# Terminal 1: Start the health dashboard
python dashboard/health_dashboard.py

# Terminal 2: Run the self-healer (3 cycles, simulated)
SELF_HEALER_SIMULATE=true python agent/healer.py
```

## Recording Script (60 seconds)

### [0:00-0:05] Hook

**Show:** The NeverZero health dashboard at `http://localhost:8080` — a dark-themed real-time metrics dashboard.

**Say:** "This is NeverZero, a real-time AI platform. But who watches the watcher?"

### [0:05-0:15] Problem

**Show:** Dashboard showing error counts and auth failures. The numbers are red.

**Say:** "When auth fails, events drop, and Redis cache goes stale, someone has to fix it. Usually a human. Usually at 3 AM."

### [0:15-0:35] Solution — The Agent

**Show:** Terminal running `python agent/healer.py`. The output shows:

```
============================================================
NeverZero Self-Healer Started
Mode: SIMULATION
Poll Interval: 30s
NeverZero Base: http://localhost:3000
============================================================

[SelfHealer] Starting monitoring cycle...
[SelfHealer] Dashboard captured
[SelfHealer] Context gathered:
System Health: healthy
Recent Error Events: 47
Auth Failures (24h): 12
...

[SelfHealer] Agent reasoning:
ALERT: Detected 47 failed auth events in the last 5 minutes.
The auth service URL may be misconfigured.
SUGGESTED FIX: Update the auth service URL to the correct endpoint.

[SelfHealer] Fix applied: fix_auth_service_url
[SelfHealer] Detail: {'ok': True, 'message': 'Auth service URL updated to https://pulse.ayushojha.com'}
```

**Say:** "This is the NeverZero Self-Healer. It uses Gemini 3.5 Flash Computer Use to screenshot the dashboard, analyze it, and apply fixes through the API. No human needed."

### [0:35-0:50] Technical Deep Dive

**Show:** Code split-screen: `gemini_computer_use.py` on the left, `healer.py` on the right.

**Say:** "The agent captures the dashboard, sends it to Gemini 3.5 Flash with telemetry context, gets back a diagnosis, and triggers the appropriate fix — auth reconfiguration, cache clearing, or compaction."

### [0:50-0:58] Result

**Show:** Dashboard refreshing — error counts drop to zero, status goes green.

**Say:** "The system healed itself. From detection to fix in under 30 seconds."

### [0:58-1:00] Close

**Show:** Final screen — repo URL, hackathon logo, team name.

**Say:** "NeverZero Self-Healer. The platform that fixes itself."

## Post-Recording Checklist

- [ ] Video is under 60 seconds
- [ ] Clearly shows the code running
- [ ] Highlights Gemini 3.5 Flash Computer Use integration
- [ ] Shows the fix being applied and the dashboard improving
- [ ] Repo is public
- [ ] All team members added to submission

## Tips

- Use a screen recorder with system audio (e.g., OBS, QuickTime, Loom)
- Keep terminal font size large (14pt+)
- Use a dark theme for code
- Speak clearly and concisely
- Show the actual output, not just slides
