"""Swappable Computer Use backend.

One enum to switch between Kimi and Gemini. Everything else stays the same:
same Playwright browser, same action execution, same verification loop.

Usage:
    export BACKEND=KIMI  # or GEMINI
    python agent/healer.py
"""
import os
import json
import base64
from enum import Enum
from typing import Any, Dict, List, Optional
import requests

from playwright.sync_api import sync_playwright, Page

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8080")


class Backend(Enum):
    KIMI = "kimi"
    GEMINI = "gemini"


class ComputerUseAgent:
    """Unified Computer Use agent. Swap LLM backend, keep everything else."""

    def __init__(self, backend: Optional[Backend] = None, headless: bool = True):
        self.backend = backend or self._detect_backend()
        self.headless = headless
        self.page: Optional[Page] = None
        self._init_browser()
        self._init_llm()

    def _detect_backend(self) -> Backend:
        env = os.getenv("BACKEND", "").lower()
        if "kimi" in env:
            return Backend.KIMI
        elif "gemini" in env:
            return Backend.GEMINI
        # Default to KIMI if no env set, since it's easier to test
        return Backend.KIMI

    def _init_llm(self):
        if self.backend == Backend.KIMI:
            self.api_key = os.getenv("KIMI_API_KEY")
            self.base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
            self.model = os.getenv("KIMI_MODEL", "kimi-latest")
            if not self.api_key:
                raise RuntimeError("Set KIMI_API_KEY for KIMI backend")
        elif self.backend == Backend.GEMINI:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
            self.model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-preview-07-2026")
            if not self.api_key:
                raise RuntimeError("Set GOOGLE_API_KEY for GEMINI backend")

    def _init_browser(self):
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page(viewport={"width": 1280, "height": 800})
        self.page.goto(DASHBOARD_URL)
        print(f"[Agent] Browser opened at {DASHBOARD_URL}")

    def screenshot(self) -> str:
        """Take screenshot and return base64."""
        png = self.page.screenshot()
        return base64.b64encode(png).decode()

    def _call_kimi(self, messages: List[Dict]) -> str:
        """Call Kimi API and return text response."""
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
        return resp.json()["choices"][0]["message"]["content"]

    def _call_gemini(self, contents: List[Dict]) -> str:
        """Call Gemini API and return text response."""
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
            "tools": [{
                "functionDeclarations": [{
                    "name": "computer_use",
                    "description": "Execute a UI action",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["click", "type", "scroll", "keypress", "done"]},
                            "x": {"type": "number"},
                            "y": {"type": "number"},
                            "text": {"type": "string"},
                            "direction": {"type": "string", "enum": ["up", "down"]},
                            "key": {"type": "string"},
                        },
                        "required": ["action"],
                    },
                }]
            }],
        }
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Extract text from Gemini response
        parts = data["candidates"][0]["content"]["parts"]
        for part in parts:
            if "text" in part:
                return part["text"]
            if "functionCall" in part:
                return json.dumps(part["functionCall"]["args"])
        return json.dumps(parts)

    def analyze(self, task: str) -> Dict[str, Any]:
        """
        Analyze current screenshot and return structured action.
        Same interface regardless of backend.
        """
        screenshot_b64 = self.screenshot()

        system_prompt = """You are a computer use agent. You control a browser via screenshots and UI actions.

Analyze the provided screenshot and return ONLY a JSON object with this exact format:
{
  "action": "click" | "type" | "scroll" | "keypress" | "done",
  "x": <number>,
  "y": <number>,
  "text": <string for type action>,
  "direction": "up" | "down" for scroll,
  "key": <string for keypress>,
  "reasoning": <brief explanation of what you see and why you're taking this action>
}

Rules:
- If the system is healthy and no action is needed, return {"action": "done", "reasoning": "HEALTHY"}
- If you see errors, describe them in reasoning and return the appropriate fix action
- Be precise with coordinates. The screen is 1280x800.
- Return ONLY valid JSON, no markdown code blocks, no explanation outside the JSON.
"""

        if self.backend == Backend.KIMI:
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}},
                        {"type": "text", "text": f"Task: {task}\n\nAnalyze this screenshot and return the JSON action."},
                    ]
                }
            ]
            raw = self._call_kimi(messages)
            # Kimi might return markdown code blocks, strip them
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("\n", 1)[0]
            if raw.startswith("json"):
                raw = raw.split("\n", 1)[1]
            return json.loads(raw)

        elif self.backend == Backend.GEMINI:
            contents = [{
                "role": "user",
                "parts": [
                    {"inlineData": {"mimeType": "image/png", "data": screenshot_b64}},
                    {"text": f"{system_prompt}\n\nTask: {task}\n\nAnalyze this screenshot and return the action JSON."},
                ]
            }]
            raw = self._call_gemini(contents)
            # Gemini might return text that includes JSON
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                import re
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    return json.loads(match.group())
                return {"action": "done", "reasoning": raw}

    def execute(self, action: Dict[str, Any]) -> str:
        """Execute a UI action via Playwright. Same for both backends."""
        act = action.get("action", "done")
        x = action.get("x", 0)
        y = action.get("y", 0)
        text = action.get("text", "")
        key = action.get("key", "")
        direction = action.get("direction", "down")

        if act == "click":
            self.page.mouse.click(x, y)
            return f"clicked at ({x}, {y})"
        elif act == "type":
            self.page.mouse.click(x, y)
            self.page.keyboard.type(text)
            return f"typed '{text}' at ({x}, {y})"
        elif act == "keypress":
            self.page.keyboard.press(key)
            return f"pressed {key}"
        elif act == "scroll":
            delta = 300 if direction == "down" else -300
            self.page.mouse.wheel(0, delta)
            return f"scrolled {direction}"
        elif act == "done":
            return "done"
        return f"unknown action: {act}"

    def run_task(self, task: str, max_steps: int = 10) -> List[Dict[str, Any]]:
        """
        Run full task: analyze → execute → verify loop.
        Same workflow regardless of backend.
        """
        history = []
        for step in range(max_steps):
            print(f"[Step {step + 1}] Analyzing screenshot...")
            action = self.analyze(task)
            reasoning = action.get("reasoning", "")
            print(f"  Reasoning: {reasoning}")

            if action.get("action") == "done":
                history.append({"step": step + 1, "action": action, "result": "done", "reasoning": reasoning})
                break

            result = self.execute(action)
            print(f"  Executed: {result}")
            history.append({"step": step + 1, "action": action, "result": result, "reasoning": reasoning})

            # Brief pause for UI to update
            import time
            time.sleep(0.5)

        return history

    def close(self):
        self.browser.close()
