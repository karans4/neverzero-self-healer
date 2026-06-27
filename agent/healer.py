"""The Self-Healer orchestrator.

Uses genuine Computer Use (Gemini 3.5 Flash + Playwright) to interact with
the NeverZero dashboard UI directly. The agent opens a browser, takes
screenshots, and the LLM generates UI actions (click, type, scroll) that
are executed via Playwright.

For Kimi (no native Computer Use), falls back to vision analysis + API calls.
"""
import os
import time
from typing import Optional

from agent.reasoning_backend import create_agent, BaseReasoningAgent
from agent.neverzero_client import NeverZeroClient

BACKEND = os.getenv("SELF_HEALER_BACKEND", "simulate").lower()
POLL_INTERVAL = int(os.getenv("SELF_HEALER_POLL_INTERVAL", "30"))
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8080")


class SelfHealer:
    """Autonomous agent that monitors NeverZero and fixes issues via UI automation."""

    def __init__(self, backend: Optional[str] = None):
        self.backend = backend or BACKEND
        self.agent: BaseReasoningAgent = create_agent(self.backend, headless=True)
        self.client = NeverZeroClient()
        self.fix_history = []

    def run_computer_use_cycle(self) -> dict:
        """Run one cycle using genuine Computer Use (Gemini + Playwright)."""
        print("\n" + "=" * 60)
        print("[SelfHealer] Starting Computer Use cycle...")

        task = (
            "Monitor the NeverZero health dashboard. If you see any errors, "
            "auth failures, or issues, click the appropriate fix button. "
            "If the dashboard shows a 'Fix Auth' button, click it. "
            "If it shows a 'Clear Cache' button, click it. "
            "After fixing, verify the dashboard shows green/healthy status."
        )

        result = self.agent.run_task(task, max_steps=10)

        # Summarize what happened
        total_steps = result.get("total_steps", 0)
        history = result.get("history", [])
        
        print(f"[SelfHealer] Completed {total_steps} steps")
        for entry in history:
            print(f"  Step {entry['step']}: {entry['reasoning'][:100]}...")
            for action in entry.get("actions", []):
                print(f"    -> {action['result']}")

        cycle = {
            "timestamp": time.time(),
            "task": task,
            "total_steps": total_steps,
            "history": history,
            "status": "done" if history and history[-1].get("status") == "done" else "incomplete",
        }
        self.fix_history.append(cycle)
        return cycle

    def run_api_cycle(self) -> dict:
        """Run one cycle using API-based fixes (Kimi or simulation)."""
        print("\n" + "=" * 60)
        print("[SelfHealer] Starting API-based cycle...")

        health = self.client.get_health()
        events = self.client.get_recent_events(limit=10)
        auth_stats = self.client.get_auth_stats()

        error_count = sum(1 for e in events if isinstance(e, dict) and e.get("event_type", "").startswith("error"))
        auth_failures = auth_stats.get("failed_attempts", 0) if isinstance(auth_stats, dict) else 0

        context = f"""System Health: {health.get("status", "unknown")}
Recent Error Events: {error_count}
Auth Failures (24h): {auth_failures}
Redis Status: {health.get("redis", "unknown")}
SpiceDB Status: {health.get("spicedb", "unknown")}
"""
        print(f"[SelfHealer] Context:\n{context}")

        # For API-based, we use a placeholder screenshot (Kimi doesn't need real UI)
        reasoning = self.agent.reason("", context)
        print(f"[SelfHealer] Agent reasoning:\n{reasoning}")

        fix = self._apply_api_fix(reasoning)
        print(f"[SelfHealer] Fix applied: {fix['action']}")

        cycle = {
            "timestamp": time.time(),
            "context": context,
            "reasoning": reasoning,
            "fix": fix,
        }
        self.fix_history.append(cycle)
        return cycle

    def _apply_api_fix(self, reasoning: str) -> dict:
        """Parse reasoning and apply API-based fix."""
        reasoning_lower = reasoning.lower()
        fix_result = {"applied": False, "action": "none", "detail": ""}

        if "HEALTHY" in reasoning:
            fix_result["applied"] = True
            fix_result["action"] = "no_action"
            fix_result["detail"] = "System is healthy"
            return fix_result

        if "auth" in reasoning_lower or "misconfigured" in reasoning_lower:
            result = self.client.fix_auth_service_url("https://pulse.ayushojha.com")
            fix_result["applied"] = True
            fix_result["action"] = "fix_auth_service_url"
            fix_result["detail"] = result
            return fix_result

        if "cache" in reasoning_lower or "stale" in reasoning_lower:
            result = self.client.clear_redis_cache("*")
            fix_result["applied"] = True
            fix_result["action"] = "clear_redis_cache"
            fix_result["detail"] = result
            return fix_result

        if "compaction" in reasoning_lower or "feature" in reasoning_lower:
            result = self.client.trigger_compaction("feat_default")
            fix_result["applied"] = True
            fix_result["action"] = "trigger_compaction"
            fix_result["detail"] = result
            return fix_result

        fix_result["action"] = "unknown"
        fix_result["detail"] = reasoning
        return fix_result

    def run_cycle(self) -> dict:
        """Run one cycle, choosing the appropriate method based on backend."""
        if self.backend == "gemini":
            return self.run_computer_use_cycle()
        else:
            return self.run_api_cycle()

    def run(self, cycles: Optional[int] = None):
        """Run the self-healer continuously or for a fixed number of cycles."""
        print("=" * 60)
        print("NeverZero Self-Healer Started")
        print(f"Backend: {self.backend}")
        print(f"Poll Interval: {POLL_INTERVAL}s")
        print(f"Dashboard URL: {DASHBOARD_URL}")
        print(f"NeverZero Base: {self.client.base_url}")
        print("=" * 60)

        cycle_count = 0
        try:
            while True:
                self.run_cycle()
                cycle_count += 1

                if cycles is not None and cycle_count >= cycles:
                    print(f"\n[SelfHealer] Completed {cycles} cycles. Exiting.")
                    break

                print(f"[SelfHealer] Sleeping {POLL_INTERVAL}s...")
                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n[SelfHealer] Interrupted by user.")
        finally:
            self.print_summary()

    def print_summary(self):
        """Print a summary of all healing cycles."""
        print("\n" + "=" * 60)
        print("SELF-HEALER SUMMARY")
        print("=" * 60)
        total = len(self.fix_history)
        fixes = sum(1 for c in self.fix_history if self._is_fix(c))
        print(f"Total cycles: {total}")
        print(f"Fixes applied: {fixes}")
        print(f"Health checks: {total - fixes}")

        if self.backend == "gemini":
            print("\nComputer Use steps:")
            for c in self.fix_history:
                steps = c.get("total_steps", 0)
                status = c.get("status", "unknown")
                print(f"  {steps} steps ({status})")
        else:
            print("\nFix breakdown:")
            actions = {}
            for c in self.fix_history:
                action = c.get("fix", {}).get("action", "unknown")
                actions[action] = actions.get(action, 0) + 1
            for action, count in actions.items():
                print(f"  {action}: {count}")
        print("=" * 60)

    def _is_fix(self, cycle: dict) -> bool:
        """Determine if a cycle resulted in a fix."""
        if self.backend == "gemini":
            return cycle.get("total_steps", 0) > 1
        else:
            fix = cycle.get("fix", {})
            return fix.get("applied", False) and fix.get("action") != "no_action"


if __name__ == "__main__":
    healer = SelfHealer()
    healer.run(cycles=3)
