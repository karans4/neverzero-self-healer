# Demo Script — 1 Minute Video

## Setup (before recording)

```bash
# Terminal 1: Start the health dashboard
python dashboard/health_dashboard.py

# Terminal 2: Run the self-healer with Gemini (3 cycles)
export GOOGLE_API_KEY="your-key"
SELF_HEALER_BACKEND=gemini python agent/healer.py
```

## Recording Script (60 seconds)

### [0:00-0:05] Hook

**Show:** The terminal starting the self-healer. Text shows:
```
NeverZero Self-Healer Started
Backend: gemini
Poll Interval: 30s
Dashboard URL: http://localhost:8080
```

**Say:** "This is NeverZero, a real-time AI platform. But who fixes it when it breaks?"

### [0:05-0:20] The Agent Opens a Browser

**Show:** Terminal output showing the agent opening a browser and taking a screenshot:

```
[SelfHealer] Starting Computer Use cycle...
[ComputerUse] Browser opened at http://localhost:8080
[Step 1] Reasoning: Screenshot shows 47 auth failures. Need to click Fix Auth button.
  -> clicked Fix Auth button at (640, 400)
[Step 2] Reasoning: Dashboard refreshed. Errors cleared. DONE.
```

**Say:** "The Self-Healer opens a real browser, takes a screenshot, and sends it to Gemini 3.5 Flash. The model analyzes the dashboard and generates actual UI actions — clicks, scrolls, types."

### [0:20-0:35] The Fix in Action

**Show:** Split screen:
- Left: The live dashboard showing red error counts
- Right: Terminal showing the agent clicking the "Fix Auth" button

**Show:** Dashboard refreshing to green after the click.

**Say:** "It sees 47 auth failures, clicks the Fix Auth button, and verifies the fix worked. All in under 30 seconds."

### [0:35-0:50] Technical Deep Dive

**Show:** Code showing the Computer Use loop:

```python
# agent/computer_use.py
screenshot = page.screenshot()
result = self._call_gemini(screenshot, task)
for action in result["actions"]:
    self._execute_action(action)  # click, type, scroll
    # verify with new screenshot
```

**Say:** "This is genuine Computer Use. Gemini returns structured actions — click at x, y — and we execute them via Playwright. Not just text suggestions. Real UI automation."

### [0:50-0:58] Result

**Show:** Dashboard fully green. Summary showing:
```
SELF-HEALER SUMMARY
Total cycles: 3
Fixes applied: 1
Health checks: 2
Computer Use steps: 3 steps (done)
```

**Say:** "The system healed itself. Detected the issue, clicked the fix, verified it worked. No human needed."

### [0:58-1:00] Close

**Show:** Final screen — repo URL, hackathon logo, team name.

**Say:** "NeverZero Self-Healer. The platform that fixes itself."

## Post-Recording Checklist

- [ ] Video is under 60 seconds
- [ ] Clearly shows the browser opening and screenshot process
- [ ] Highlights Gemini 3.5 Flash Computer Use integration
- [ ] Shows the actual click being executed and the dashboard changing
- [ ] Shows verification screenshot after the fix
- [ ] Repo is public
- [ ] All team members added to submission

## Tips

- Use a screen recorder with system audio (e.g., OBS, QuickTime, Loom)
- Keep terminal font size large (14pt+)
- Use a dark theme for code
- Speak clearly and concisely
- Show the actual browser window, not just terminal output
- The dashboard auto-refreshes every 5 seconds, so changes are visible
