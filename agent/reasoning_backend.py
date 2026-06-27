"""Generic LLM reasoning backend for the Self-Healer.

Supports both Kimi (OpenAI-compatible), Gemini 3.5 Flash Computer Use,
and simulated backends. The interface is intentionally simple: screenshot
+ context → reasoning text OR task → structured UI actions.
"""
import os
import base64
import json
from typing import Any, Dict, Optional
import requests

from agent.computer_use import GenuineComputerUseAgent, SimulatedComputerUseAgent, SimulatedPlaywrightAgent


class BaseReasoningAgent:
    """Abstract base for reasoning agents."""

    def reason(self, screenshot_b64: str, context: str) -> str:
        """Analyze a screenshot and return text reasoning."""
        raise NotImplementedError

    def run_task(self, task: str, max_steps: int = 10) -> Dict[str, Any]:
        """Execute a multi-step task with UI actions."""
        raise NotImplementedError


class KimiReasoningAgent(BaseReasoningAgent):
    """Kimi backend using OpenAI-compatible vision API.

    Requires: KIMI_API_KEY environment variable.
    """

    def __init__(self, model: str = "kimi-latest"):
        self.model = model
        self.api_key = os.getenv("KIMI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set KIMI_API_KEY environment variable")
        self.base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")

    def _call(self, messages: list) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 4096,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def reason(self, screenshot_b64: str, context: str) -> str:
        prompt = f"""You are a site reliability engineer monitoring a real-time AI platform dashboard.

Current context:
{context}

Analyze this dashboard screenshot. Identify any anomalies, errors, or issues.
If you see any problems, describe them precisely and suggest the exact fix.
If everything looks healthy, say exactly: HEALTHY

Focus on:
- Error counts or failed events
- Auth failures or permission issues
- High latency or dropped connections
- Missing or stale data
- Misconfigured service URLs
"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{screenshot_b64}"
                        }
                    },
                    {"type": "text", "text": prompt},
                ]
            }
        ]

        result = self._call(messages)
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return json.dumps(result)

    def run_task(self, task: str, max_steps: int = 10) -> Dict[str, Any]:
        # Kimi doesn't have native Computer Use, so we use reason-only
        return {
            "task": task,
            "total_steps": 1,
            "history": [{
                "step": 1,
                "reasoning": self.reason("", task),
                "actions": [],
                "status": "done"
            }],
            "final_screenshot": "",
        }


class GeminiReasoningAgent(BaseReasoningAgent):
    """Gemini 3.5 Flash Computer Use backend.

    Uses Gemini's native Computer Use tool for screenshot → UI actions.
    Requires: GOOGLE_API_KEY environment variable.
    """

    def __init__(self, model: str = "gemini-3.5-flash-preview-07-2026", headless: bool = True):
        self.model = model
        self.agent = GenuineComputerUseAgent(model=model, headless=headless)

    def reason(self, screenshot_b64: str, context: str) -> str:
        return self.agent.check_health()

    def run_task(self, task: str, max_steps: int = 10) -> Dict[str, Any]:
        return self.agent.run_task(task, max_steps=max_steps)


class SimulatedReasoningAgent(BaseReasoningAgent):
    """Fallback that simulates reasoning for demo/testing."""

    def __init__(self, use_playwright_sim: bool = False):
        self.call_count = 0
        if use_playwright_sim:
            self.sim = SimulatedPlaywrightAgent()
        else:
            self.sim = SimulatedComputerUseAgent()

    def reason(self, screenshot_b64: str, context: str) -> str:
        self.call_count += 1
        return self.sim.check_health()

    def run_task(self, task: str, max_steps: int = 10) -> Dict[str, Any]:
        return self.sim.run_task(task, max_steps)


def create_agent(backend: Optional[str] = None, headless: bool = True) -> BaseReasoningAgent:
    """Factory: create the appropriate reasoning agent.

    Args:
        backend: "kimi", "gemini", or "simulate". Auto-detected from env if None.
        headless: Whether to run Playwright in headless mode (for Gemini).
    """
    if backend is None:
        if os.getenv("GOOGLE_API_KEY"):
            backend = "gemini"
        elif os.getenv("KIMI_API_KEY"):
            backend = "kimi"
        else:
            backend = "simulate"

    backend = backend.lower()
    if backend == "kimi":
        return KimiReasoningAgent()
    elif backend == "gemini":
        return GeminiReasoningAgent(headless=headless)
    elif backend == "simulate":
        return SimulatedReasoningAgent(use_playwright_sim=True)
    else:
        raise ValueError(f"Unknown backend: {backend}. Use 'kimi', 'gemini', or 'simulate'.")
