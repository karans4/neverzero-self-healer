"""Text-based Self-Healer — no vision, no browser, just JSON metrics + LLM reasoning.

Usage:
    BACKEND=KIMI KIMI_API_KEY=xxx python3 agent/healer.py
    BACKEND=GEMINI GOOGLE_API_KEY=xxx python3 agent/healer.py
    BACKEND=SIMULATE python3 agent/healer.py

The agent reads metrics from the dashboard API, reasons with a text LLM,
and calls NeverZero admin APIs to fix issues. No screenshots, no Playwright.
"""
import os
import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional
import requests

from agent.neverzero_client import NeverZeroClient


class Backend(Enum):
    KIMI = "kimi"
    GEMINI = "gemini"
    SIMULATE = "simulate"


class TextReasoningAgent:
    """Text-only reasoning agent. No vision, no browser."""

    def __init__(self, backend: Optional[Backend] = None):
        self.backend = backend or self._detect_backend()
        self._init_llm()
        self.fix_count = 0

    def _detect_backend(self) -> Backend:
        env = os.getenv("BACKEND", "simulate").lower()
        if "kimi" in env:
            return Backend.KIMI
        elif "gemini" in env:
            return Backend.GEMINI
        return Backend.SIMULATE

    def _init_llm(self):
        if self.backend == Backend.KIMI:
            self.api_key = os.getenv("KIMI_API_KEY")
            raw_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
            self.base_url = raw_url.rstrip("/")
            self.model = os.getenv("KIMI_MODEL", "kimi-for-coding")
            if not self.api_key:
                raise RuntimeError("Set KIMI_API_KEY for KIMI backend")
        elif self.backend == Backend.GEMINI:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
            self.model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-preview-07-2026")
            if not self.api_key:
                raise RuntimeError("Set GOOGLE_API_KEY for GEMINI backend")

    def _call_kimi(self, messages: List[Dict]) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 1,  # kimi-for-coding only allows 1
            "max_tokens": 4096,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        msg = data["choices"][0]["message"]
        # kimi-for-coding returns reasoning in reasoning_content, not content
        content = msg.get("content", "")
        reasoning = msg.get("reasoning_content", "")
        return content or reasoning or ""

    def _call_gemini(self, contents: List[Dict]) -> str:
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
        }
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def reason(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze metrics and return structured fix decision.

        Returns:
            {
                "action": "no_action" | "fix_auth" | "clear_cache" | "trigger_compaction",
                "reasoning": "...",
                "confidence": 0.0-1.0
            }
        """
        metrics_text = json.dumps(metrics, indent=2)

        system_prompt = """You are a Site Reliability Engineer monitoring a real-time AI platform.

You receive JSON metrics from the platform. Analyze them and decide what to do.

Return ONLY a JSON object with this exact format:
{
  "action": "no_action" | "fix_auth" | "clear_cache" | "trigger_compaction",
  "reasoning": "brief explanation of what you found and why you're taking this action",
  "confidence": 0.0-1.0
}

Rules:
- If system_status is "healthy" and error_count is 0, return {"action": "no_action", "reasoning": "HEALTHY", "confidence": 1.0}
- If auth_failures > 5 or error_count > 10, return {"action": "fix_auth", ...}
- If redis_status is not "connected" or system_status is "degraded", return {"action": "clear_cache", ...}
- If events_per_minute > 100, return {"action": "trigger_compaction", ...}
- Return ONLY valid JSON, no markdown, no explanation outside the JSON.
"""

        if self.backend == Backend.KIMI:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Current metrics:\n{metrics_text}\n\nWhat should I do?"}
            ]
            raw = self._call_kimi(messages)

        elif self.backend == Backend.GEMINI:
            contents = [{
                "role": "user",
                "parts": [
                    {"text": f"{system_prompt}\n\nCurrent metrics:\n{metrics_text}\n\nWhat should I do?"}
                ]
            }]
            raw = self._call_gemini(contents)

        else:  # SIMULATE
            self.fix_count += 1
            if self.fix_count % 3 == 0:
                return {
                    "action": "fix_auth",
                    "reasoning": "ALERT: 47 auth failures detected. Auth service URL may be misconfigured.",
                    "confidence": 0.95
                }
            return {
                "action": "no_action",
                "reasoning": "HEALTHY",
                "confidence": 1.0
            }

        # Parse JSON from text (strip markdown code blocks if present)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("\n", 1)[0]
        if raw.startswith("json"):
            raw = raw.split("\n", 1)[1]

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from text
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"action": "no_action", "reasoning": raw, "confidence": 0.5}


class TextSelfHealer:
    """Text-based self-healer. No vision, no browser."""

    def __init__(self, backend: Optional[Backend] = None):
        self.backend = backend or self._detect_backend()
        self.agent = TextReasoningAgent(backend=self.backend)
        self.client = NeverZeroClient()
        self.history = []

    def _detect_backend(self) -> Backend:
        env = os.getenv("BACKEND", "simulate").lower()
        if "kimi" in env:
            return Backend.KIMI
        elif "gemini" in env:
            return Backend.GEMINI
        return Backend.SIMULATE

    def run_cycle(self) -> Dict[str, Any]:
        """Run one monitoring and healing cycle."""
        print("\n" + "=" * 60)
        print("[SelfHealer] Starting cycle...")

        # Step 1: Fetch metrics
        metrics = self.client.get_health()
        
        # Use simulated metrics if API is down or returns error
        if not isinstance(metrics, dict) or "error" in metrics or metrics.get("status") == "error":
            print("[SelfHealer] NeverZero API unavailable, using simulated metrics")
            import random
            if random.random() < 0.3:
                metrics = {
                    "system_status": "degraded",
                    "error_count": 47,
                    "auth_failures": 12,
                    "auth_service_url": "https://pulse.ayushojha.com",
                    "redis_status": "connected",
                    "spicedb_status": "connected",
                    "events_per_minute": 42,
                    "active_sessions": 7,
                }
            else:
                metrics = {
                    "system_status": "healthy",
                    "error_count": 0,
                    "auth_failures": 0,
                    "auth_service_url": "https://pulse.ayushojha.com",
                    "redis_status": "connected",
                    "spicedb_status": "connected",
                    "events_per_minute": 42,
                    "active_sessions": 7,
                }

        print(f"[SelfHealer] Metrics: {json.dumps(metrics, indent=2)}")

        # Step 2: Reason
        decision = self.agent.reason(metrics)
        print(f"[SelfHealer] Decision: {decision['action']}")
        print(f"[SelfHealer] Reasoning: {decision['reasoning']}")
        print(f"[SelfHealer] Confidence: {decision.get('confidence', 0.5)}")

        # Step 3: Apply fix
        fix_result = self._apply_fix(decision["action"])
        print(f"[SelfHealer] Fix result: {fix_result}")

        cycle = {
            "timestamp": time.time(),
            "metrics": metrics,
            "decision": decision,
            "fix_result": fix_result,
        }
        self.history.append(cycle)
        return cycle

    def _apply_fix(self, action: str) -> Dict[str, Any]:
        """Apply the fix action."""
        if action == "no_action":
            return {"ok": True, "message": "No action needed"}
        elif action == "fix_auth":
            return self.client.fix_auth_service_url("https://pulse.ayushojha.com")
        elif action == "clear_cache":
            return self.client.clear_redis_cache("*")
        elif action == "trigger_compaction":
            return self.client.trigger_compaction("feat_default")
        return {"ok": False, "error": f"Unknown action: {action}"}

    def run(self, cycles: Optional[int] = None):
        """Run continuously or for a fixed number of cycles."""
        print("=" * 60)
        print("NeverZero Text Self-Healer")
        print(f"Backend: {self.backend.value}")
        print(f"Poll Interval: {os.getenv('POLL_INTERVAL', '30')}s")
        print("=" * 60)

        cycle_count = 0
        try:
            while True:
                self.run_cycle()
                cycle_count += 1

                if cycles is not None and cycle_count >= cycles:
                    print(f"\n[SelfHealer] Completed {cycles} cycles. Exiting.")
                    break

                poll_interval = int(os.getenv("POLL_INTERVAL", "30"))
                print(f"[SelfHealer] Sleeping {poll_interval}s...")
                time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n[SelfHealer] Interrupted by user.")
        finally:
            self.print_summary()

    def print_summary(self):
        """Print summary of all cycles."""
        print("\n" + "=" * 60)
        print("SELF-HEALER SUMMARY")
        print("=" * 60)
        total = len(self.history)
        fixes = sum(1 for c in self.history if c["decision"]["action"] != "no_action")
        print(f"Total cycles: {total}")
        print(f"Fixes applied: {fixes}")
        print(f"Health checks: {total - fixes}")

        actions = {}
        for c in self.history:
            action = c["decision"]["action"]
            actions[action] = actions.get(action, 0) + 1
        for action, count in actions.items():
            print(f"  {action}: {count}")
        print("=" * 60)


if __name__ == "__main__":
    healer = TextSelfHealer()
    healer.run(cycles=3)
