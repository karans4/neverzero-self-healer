"""The Self-Healer orchestrator.

Combines Gemini 3.5 Flash Computer Use with the NeverZero API to create
an autonomous agent that detects and fixes issues in real-time.
"""
import os
import time
import base64
from typing import Optional

from agent.gemini_computer_use import GeminiComputerUseAgent, SimulatedComputerUseAgent
from agent.neverzero_client import NeverZeroClient

SIMULATE = os.getenv("SELF_HEALER_SIMULATE", "false").lower() == "true"
POLL_INTERVAL = int(os.getenv("SELF_HEALER_POLL_INTERVAL", "30"))


class SelfHealer:
    """Autonomous agent that monitors NeverZero and fixes issues."""

    def __init__(self):
        if SIMULATE:
            print("[SelfHealer] Running in SIMULATION mode (no Gemini API calls)")
            self.agent = SimulatedComputerUseAgent()
        else:
            print("[SelfHealer] Running with Gemini 3.5 Flash Computer Use")
            self.agent = GeminiComputerUseAgent()

        self.client = NeverZeroClient()
        self.fix_history = []

    def capture_dashboard(self) -> str:
        """Capture a screenshot of the NeverZero dashboard."""
        # In a real deployment, this would use Playwright/Selenium to take
        # a screenshot of the running dashboard. For the hackathon, we
        # simulate with a base64-encoded placeholder or use a local file.
        #
        # TODO: Replace with actual Playwright screenshot:
        # from playwright.sync_api import sync_playwright
        # with sync_playwright() as p:
        #     browser = p.chromium.launch()
        #     page = browser.new_page()
        #     page.goto("http://localhost:3000/dashboard")
        #     screenshot = page.screenshot()
        #     browser.close()
        #     return base64.b64encode(screenshot).decode()

        # For demo purposes, return a simulated screenshot
        placeholder_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        return placeholder_png

    def gather_context(self) -> str:
        """Gather telemetry context for the agent."""
        health = self.client.get_health()
        events = self.client.get_recent_events(limit=10)
        auth_stats = self.client.get_auth_stats()

        # Count errors in recent events
        error_count = sum(1 for e in events if isinstance(e, dict) and e.get("event_type", "").startswith("error"))
        auth_failures = auth_stats.get("failed_attempts", 0) if isinstance(auth_stats, dict) else 0

        context = f"""System Health: {health.get("status", "unknown")}
Recent Error Events: {error_count}
Auth Failures (24h): {auth_failures}
Auth Service URL: {auth_stats.get("auth_service_url", "unknown") if isinstance(auth_stats, dict) else "unknown"}
Redis Status: {health.get("redis", "unknown")}
SpiceDB Status: {health.get("spicedb", "unknown")}
"""
        return context

    def apply_fix(self, reasoning: str) -> dict:
        """Parse the agent's reasoning and apply the appropriate fix."""
        reasoning_lower = reasoning.lower()
        fix_result = {"applied": False, "action": "none", "detail": ""}

        if "HEALTHY" in reasoning:
            fix_result["applied"] = True
            fix_result["action"] = "no_action"
            fix_result["detail"] = "System is healthy, no action needed"
            return fix_result

        # Auth service URL fix
        if "auth service url" in reasoning_lower or "misconfigured" in reasoning_lower:
            result = self.client.fix_auth_service_url("https://pulse.ayushojha.com")
            fix_result["applied"] = True
            fix_result["action"] = "fix_auth_service_url"
            fix_result["detail"] = result
            return fix_result

        # Redis cache clear
        if "stale data" in reasoning_lower or "cache" in reasoning_lower:
            result = self.client.clear_redis_cache("*")
            fix_result["applied"] = True
            fix_result["action"] = "clear_redis_cache"
            fix_result["detail"] = result
            return fix_result

        # Compaction trigger
        if "compaction" in reasoning_lower or "feature" in reasoning_lower:
            # Extract feature ID from reasoning if present
            feature_id = "feat_default"  # fallback
            result = self.client.trigger_compaction(feature_id)
            fix_result["applied"] = True
            fix_result["action"] = "trigger_compaction"
            fix_result["detail"] = result
            return fix_result

        # Unknown issue — log for human review
        fix_result["applied"] = False
        fix_result["action"] = "unknown"
        fix_result["detail"] = reasoning
        return fix_result

    def run_cycle(self) -> dict:
        """Run one full monitoring and healing cycle."""
        print("\n" + "=" * 60)
        print("[SelfHealer] Starting monitoring cycle...")

        # Step 1: Capture dashboard
        screenshot = self.capture_dashboard()
        print("[SelfHealer] Dashboard captured")

        # Step 2: Gather context
        context = self.gather_context()
        print(f"[SelfHealer] Context gathered:\n{context}")

        # Step 3: Agent reasoning with Computer Use
        reasoning = self.agent.reason(screenshot, context)
        print(f"[SelfHealer] Agent reasoning:\n{reasoning}")

        # Step 4: Apply fix if needed
        fix = self.apply_fix(reasoning)
        print(f"[SelfHealer] Fix applied: {fix['action']}")
        if fix["detail"]:
            print(f"[SelfHealer] Detail: {fix['detail']}")

        # Step 5: Log to history
        cycle = {
            "timestamp": time.time(),
            "context": context,
            "reasoning": reasoning,
            "fix": fix,
        }
        self.fix_history.append(cycle)

        return cycle

    def run(self, cycles: Optional[int] = None):
        """Run the self-healer continuously or for a fixed number of cycles."""
        print("=" * 60)
        print("NeverZero Self-Healer Started")
        print(f"Mode: {'SIMULATION' if SIMULATE else 'LIVE (Gemini 3.5 Flash)'}")
        print(f"Poll Interval: {POLL_INTERVAL}s")
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
        fixes = sum(1 for c in self.fix_history if c["fix"]["applied"])
        print(f"Total cycles: {total}")
        print(f"Fixes applied: {fixes}")
        print(f"Health checks: {total - fixes}")
        print("\nFix breakdown:")
        actions = {}
        for c in self.fix_history:
            action = c["fix"]["action"]
            actions[action] = actions.get(action, 0) + 1
        for action, count in actions.items():
            print(f"  {action}: {count}")
        print("=" * 60)


if __name__ == "__main__":
    healer = SelfHealer()
    healer.run(cycles=3)  # Run 3 cycles for demo
