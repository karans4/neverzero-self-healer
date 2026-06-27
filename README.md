# NeverZero Self-Healer

> **Autonomous platform healing using Gemini 3.5 Flash Computer Use**

A self-improving AI system that monitors the [NeverZero](https://github.com/ayushozha/NeverZero) real-time platform, detects anomalies via screenshot analysis, and applies fixes without human intervention.

## 🎯 Hackathon Theme

**The Self-Improvement Stack** — infrastructure for continuously evaluating, monitoring, and upgrading AI systems at scale.

## 🚀 What It Does

1. **Captures** a screenshot of the NeverZero health dashboard
2. **Analyzes** it using Gemini 3.5 Flash Computer Use (screenshot → reasoning → actions)
3. **Gathers** telemetry context (health, events, auth stats)
4. **Reasons** about anomalies and decides on a fix
5. **Applies** the fix via NeverZero admin APIs (auth config, cache clearing, compaction)
6. **Logs** everything for continual learning and auditability

## 🛠️ Built With

- **Gemini 3.5 Flash** — Computer Use for visual dashboard analysis and UI action generation
- **NeverZero** — Real-time event platform being monitored (existing infrastructure)
- **Python** — Agent orchestration and API integration

## 📦 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key
export GOOGLE_API_KEY="your-key-here"

# Start the health dashboard
python dashboard/health_dashboard.py &

# Run the self-healer (3 cycles for demo)
python agent/healer.py
```

## 🎥 Demo

See the agent in action: it detects issues from the dashboard, reasons about them, and fixes them autonomously.

[Demo video link — 1 minute]

## 🏆 Prize Category

**Best Usage of Gemini 3.5** ($5,000)

Uses **Computer Use in Gemini 3.5 Flash** to:
- Analyze dashboard screenshots visually
- Detect anomalies (auth failures, errors, stale data)
- Generate and execute fix actions via API calls

## 📁 Project Structure

```
neverzero-self-healer/
├── agent/
│   ├── gemini_computer_use.py   # Gemini 3.5 Flash Computer Use integration
│   ├── neverzero_client.py      # NeverZero API client
│   └── healer.py                # Main self-healing orchestrator
├── dashboard/
│   └── health_dashboard.py      # Real-time metrics dashboard
├── skills/
│   ├── AGENTS.md                # Agent persona (required for Gemini prize)
│   └── SKILL.md                 # Technical skill documentation
├── demo/
│   └── demo_script.md           # Script for 1-minute demo video
└── README.md                    # This file
```

## 🧠 How It Works

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

## 📝 Key Features Built During Hackathon

- **Visual anomaly detection** via Gemini 3.5 Flash Computer Use screenshots
- **Autonomous healing** — no human in the loop for known issue types
- **Contextual reasoning** — combines visual + telemetry data for diagnosis
- **Audit trail** — every cycle, observation, and fix is logged
- **Extensible fix catalog** — easy to add new fix types

## 👥 Team

- [Your name] — AI Engineer

## 🔗 Links

- **NeverZero Platform:** https://github.com/ayushozha/NeverZero
- **Hackathon:** https://cerebralvalley.ai/e/aiewf-hackathon-2026
- **Gemini 3.5 Flash:** https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.5

## 📄 License

MIT
