"""Gemini 3.5 Flash Computer Use integration.

Uses the Gemini API to take screenshots of a dashboard and generate
UI actions (click, type, scroll) to interact with it autonomously.

Requires: GOOGLE_API_KEY environment variable.
"""
import os
import base64
import json
import time
from typing import Any, Dict, List, Optional
import requests

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Set GOOGLE_API_KEY environment variable")

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
COMPUTER_USE_MODEL = "gemini-3.5-flash-preview-07-2026"


class GeminiComputerUseAgent:
    """Agent that uses Gemini 3.5 Flash Computer Use to interact with a web UI."""

    def __init__(self, model: str = COMPUTER_USE_MODEL):
        self.model = model
        self.session_url = None
        self.history: List[Dict[str, Any]] = []

    def _call(self, contents: List[Dict[str, Any]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Make a Gemini API call."""
        url = f"{GEMINI_BASE_URL}/{self.model}:generateContent?key={GEMINI_API_KEY}"
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192,
            },
        }
        if tools:
            payload["tools"] = tools

        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def analyze_screenshot(self, screenshot_b64: str, prompt: str) -> Dict[str, Any]:
        """Analyze a screenshot and return the agent's reasoning + actions."""
        content = {
            "role": "user",
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": screenshot_b64,
                    }
                },
                {"text": prompt},
            ],
        }

        # Computer Use tool definition
        computer_use_tool = {
            "functionDeclarations": [
                {
                    "name": "computer_use",
                    "description": "Execute a computer action (click, type, scroll, screenshot)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["click", "type", "scroll", "screenshot", "keypress"],
                                "description": "The action to perform",
                            },
                            "x": {"type": "number", "description": "X coordinate for click"},
                            "y": {"type": "number", "description": "Y coordinate for click"},
                            "text": {"type": "string", "description": "Text to type"},
                            "direction": {
                                "type": "string",
                                "enum": ["up", "down"],
                                "description": "Scroll direction",
                            },
                            "key": {"type": "string", "description": "Key to press (e.g., Enter, Escape)"},
                        },
                        "required": ["action"],
                    },
                }
            ]
        }

        result = self._call([content], tools=[computer_use_tool])
        return result

    def reason(self, screenshot_b64: str, context: str) -> str:
        """High-level reasoning: what's wrong and what should we do?"""
        prompt = f"""You are a site reliability engineer monitoring a real-time AI platform dashboard.

Current context: {context}

Analyze this dashboard screenshot. Identify any anomalies, errors, or issues.
If you see any problems, describe them precisely and suggest the exact fix.
If everything looks healthy, say "HEALTHY".

Focus on:
- Error counts or failed events
- Auth failures or permission issues
- High latency or dropped connections
- Missing or stale data
"""
        result = self.analyze_screenshot(screenshot_b64, prompt)
        try:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text
        except (KeyError, IndexError):
            return json.dumps(result)


class SimulatedComputerUseAgent:
    """Fallback that simulates Computer Use for demo/testing without API calls."""

    def __init__(self):
        self.call_count = 0

    def reason(self, screenshot_b64: str, context: str) -> str:
        self.call_count += 1
        # Simulate detecting an issue every 3rd call
        if self.call_count % 3 == 0:
            return (
                "ALERT: Detected 47 failed auth events in the last 5 minutes. "
                "The auth service URL may be misconfigured. "
                "SUGGESTED FIX: Update the auth service URL to the correct endpoint."
            )
        return "HEALTHY"
