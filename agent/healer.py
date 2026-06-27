"""Simple self-healer using swappable Computer Use backend.

Usage:
    BACKEND=KIMI KIMI_API_KEY=xxx python3 agent/healer.py
    BACKEND=GEMINI GOOGLE_API_KEY=xxx python3 agent/healer.py
"""
import os
from agent.computer_use import ComputerUseAgent, Backend


def main():
    backend = Backend(os.getenv("BACKEND", "kimi").lower())
    print(f"=" * 60)
    print(f"NeverZero Self-Healer")
    print(f"Backend: {backend.value}")
    print(f"Dashboard: http://localhost:8080")
    print(f"=" * 60)

    agent = ComputerUseAgent(backend=backend, headless=True)

    try:
        task = (
            "Monitor the NeverZero health dashboard. "
            "If you see auth failures or errors, click the Fix Auth button. "
            "If the dashboard is healthy, you're done."
        )
        history = agent.run_task(task, max_steps=5)

        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")
        for h in history:
            print(f"Step {h['step']}: {h['action'].get('action', '?')} → {h['result']}")
            print(f"  Reasoning: {h['reasoning'][:100]}...")

    finally:
        agent.close()


if __name__ == "__main__":
    main()
