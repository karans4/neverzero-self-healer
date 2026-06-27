# NeverZero Self-Healer

> **Autonomous platform healing using Gemini 3.5 Flash Computer Use**

A self-improving AI system that monitors the [NeverZero](https://github.com/ayushozha/NeverZero) real-time platform, detects anomalies via screenshot analysis, **and clicks actual UI buttons to fix them** — without human intervention.

## 🎯 Hackathon Theme

**The Self-Improvement Stack** — infrastructure for continuously evaluating, monitoring, and upgrading AI systems at scale.

## 🚀 What It Does

1. **Opens** the NeverZero health dashboard in a headless browser (Playwright)
2. **Takes a screenshot** and sends it to Gemini 3.5 Flash
3. **Gemini analyzes** the screenshot using Computer Use and returns structured UI actions
4. **Executes** those actions via Playwright — clicks "Fix Auth" buttons, scrolls, types
5. **Verifies** by taking another screenshot after the fix
6. **Logs everything** for continual learning and auditability

This is **genuine Computer Use** — the model generates "click at (x, y)" and we execute it on the real UI. Not just vision analysis.

## 🛠️ Built With

- **Gemini 3.5 Flash** — Computer Use for visual dashboard analysis and UI action generation
- **Playwright** — Browser automation that executes the model's UI actions
- **NeverZero** — Real-time event platform being monitored (existing infrastructure)
- **Python** — Agent orchestration

## 📦 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set your Gemini API key
export GOOGLE_API_KEY="your-key-here"

# Start the health dashboard
python dashboard/health_dashboard.py &

# Run the self-healer (3 cycles for demo)
SELF_HEALER_BACKEND=gemini python agent/healer.py
```

## 🎥 Demo

See the agent open a browser, screenshot the dashboard, detect issues, and click fix buttons autonomously.

[Demo video link — 1 minute]

## 🏆 Prize Category

**Best Usage of Gemini 3.5** ($5,000)

Uses **Computer Use in Gemini 3.5 Flash** to:
- Take screenshots of the running dashboard
- Detect anomalies visually (auth failures, errors)
- Generate structured UI actions (click, type, scroll)
- Execute them via Playwright browser automation

## 📁 Project Structure

```
neverzero-self-healer/
├── agent/
│   ├── computer_use.py          # Genuine Computer Use: Gemini + Playwright
│   ├── reasoning_backend.py     # Backend abstraction (Kimi / Gemini / simulate)
│   ├── neverzero_client.py      # NeverZero API client (fallback)
│   └── healer.py                # Main orchestrator
├── dashboard/
│   └── health_dashboard.py      # Interactive dashboard with Fix Auth / Clear Cache buttons
├── skills/
│   ├── AGENTS.md                # Agent persona (required for Gemini prize)
│   └── SKILL.md                 # Technical skill documentation
├── demo/
│   └── demo_script.md           # Script for 1-minute demo video
└── README.md                    # This file
```

## 🧠 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  Gemini 3.5 Flash Computer Use                              │
│  ┌──────────────┐     ┌──────────────┐    ┌──────────────┐ │
│  │ Screenshot   │────▶│ Analyze UI   │───▶│ Generate     │ │
│  │              │     │              │    │ Actions      │ │
│  └──────────────┘     └──────────────┘    └──────────────┘ │
│         ▲                                           │       │
│         │                                           │       │
│  Playwright                                         │       │
│  ┌──────────────┐     ┌──────────────┐              │       │
│  │ Execute      │◀────│ Click / Type │◀─────────────┘       │
│  │ Actions      │     │ / Scroll     │                      │
│  └──────────────┘     └──────────────┘                      │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │ Dashboard    │                                          │
│  │ (localhost) │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

## 🔑 Key Features Built During Hackathon

- **Genuine Computer Use** — model generates click coordinates, not just text suggestions
- **Playwright automation** — executes real UI actions on a live browser
- **Visual verification** — takes post-fix screenshots to confirm the fix worked
- **Multi-step reasoning** — agent iterates: screenshot → reason → act → verify
- **Extensible** — easy to add new dashboard buttons and fix types

## 📝 Computer Use Example

The Gemini model returns structured actions like:

```json
{
  "action": "click",
  "x": 640,
  "y": 400
}
```

The agent executes this via Playwright:

```python
page.mouse.click(640, 400)
```

Then takes another screenshot to verify the fix.

## 👥 Team

- [Your name] — AI Engineer

## 🔗 Links

- **NeverZero Platform:** https://github.com/ayushozha/NeverZero
- **Hackathon:** https://cerebralvalley.ai/e/aiewf-hackathon-2026
- **Gemini 3.5 Flash:** https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.5

## 📄 License

MIT
