"""Genuine Computer Use agent using Playwright + Gemini 3.5 Flash.

This agent opens the dashboard in a real browser, takes screenshots,
and uses Gemini's Computer Use API to generate UI actions (click, type, scroll)
that it then executes via Playwright.

This is the REAL Computer Use feature, not just vision analysis.
"""
import os
import base64
import json
from typing import Any, Dict, List, Optional
import requests

from playwright.sync_api import sync_playwright, Page, Browser

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
COMPUTER_USE_MODEL = "gemini-3.5-flash-preview-07-2026"

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8080")


class GenuineComputerUseAgent:
    """Agent that uses Gemini 3.5 Flash Computer Use to interact with a real UI via Playwright."""

    def __init__(self, model: str = COMPUTER_USE_MODEL, headless: bool = True):
        self.model = model
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        if not GEMINI_API_KEY:
            raise RuntimeError("Set GOOGLE_API_KEY environment variable")

    def _init_browser(self):
        """Initialize Playwright browser."""
        if self.browser is None:
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page(viewport={"width": 1280, "height": 800})
            self.page.goto(DASHBOARD_URL)
            print(f"[ComputerUse] Browser opened at {DASHBOARD_URL}")

    def _close_browser(self):
        """Close Playwright browser."""
        if self.browser:
            self.browser.close()
            self.browser = None
            self.page = None

    def _call_gemini(self, contents: List[Dict[str, Any]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
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

    def _screenshot(self) -> str:
        """Take a screenshot and return base64."""
        if self.page is None:
            self._init_browser()
        screenshot_bytes = self.page.screenshot()
        return base64.b64encode(screenshot_bytes).decode()

    def _execute_action(self, action: Dict[str, Any]) -> str:
        """Execute a UI action via Playwright."""
        if self.page is None:
            return "error: browser not initialized"

        action_type = action.get("action")
        x = action.get("x", 0)
        y = action.get("y", 0)
        text = action.get("text", "")
        key = action.get("key", "")
        direction = action.get("direction", "down")
        scroll_amount = action.get("scroll_amount", 300)

        if action_type == "click":
            self.page.mouse.click(x, y)
            return f"clicked at ({x}, {y})"

        elif action_type == "type":
            self.page.mouse.click(x, y)  # Focus the element
            self.page.keyboard.type(text)
            return f"typed '{text}' at ({x}, {y})"

        elif action_type == "keypress":
            self.page.keyboard.press(key)
            return f"pressed key: {key}"

        elif action_type == "scroll":
            delta = scroll_amount if direction == "down" else -scroll_amount
            self.page.mouse.wheel(0, delta)
            return f"scrolled {direction} by {scroll_amount}"

        elif action_type == "screenshot":
            # Already takes screenshot automatically
            return "screenshot taken"

        elif action_type == "wait":
            import time
            wait_time = action.get("wait_time", 1)
            time.sleep(wait_time)
            return f"waited {wait_time}s"

        else:
            return f"unknown action: {action_type}"

    def run_task(self, task: str, max_steps: int = 10) -> Dict[str, Any]:
        """
        Run a task using Computer Use.
        
        The agent takes a screenshot, sends it to Gemini with the Computer Use tool,
        gets back a list of actions, executes them, and repeats until the task is done.
        """
        self._init_browser()

        # Computer Use tool definition
        computer_use_tool = {
            "functionDeclarations": [
                {
                    "name": "computer_use",
                    "description": "Execute a computer action on the dashboard UI",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["click", "type", "scroll", "keypress", "screenshot", "wait"],
                                "description": "The action to perform",
                            },
                            "x": {"type": "number", "description": "X coordinate for click/type"},
                            "y": {"type": "number", "description": "Y coordinate for click/type"},
                            "text": {"type": "string", "description": "Text to type"},
                            "key": {"type": "string", "description": "Key to press (e.g., Enter, Escape, Tab)"},
                            "direction": {
                                "type": "string",
                                "enum": ["up", "down"],
                                "description": "Scroll direction",
                            },
                            "scroll_amount": {"type": "number", "description": "Pixels to scroll", "default": 300},
                            "wait_time": {"type": "number", "description": "Seconds to wait", "default": 1},
                        },
                        "required": ["action"],
                    },
                }
            ]
        }

        history = []
        for step in range(max_steps):
            screenshot_b64 = self._screenshot()

            content = {
                "role": "user",
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": screenshot_b64,
                        }
                    },
                    {"text": f"Task: {task}\n\nThis is the current state of the NeverZero dashboard. Analyze the screenshot and determine what action(s) to take. Use the computer_use tool to interact with the UI. After each action, a new screenshot will be provided.\n\nWhen the task is complete, say 'DONE' in your reasoning."},
                ],
            }

            result = self._call_gemini([content], tools=[computer_use_tool])

            try:
                candidate = result["candidates"][0]
                parts = candidate["content"]["parts"]
                
                # Extract text reasoning and function calls
                reasoning = ""
                actions = []
                for part in parts:
                    if "text" in part:
                        reasoning += part["text"] + "\n"
                    elif "functionCall" in part:
                        actions.append(part["functionCall"]["args"])

                print(f"[Step {step + 1}] Reasoning: {reasoning.strip()}")
                
                if "DONE" in reasoning.upper() or not actions:
                    history.append({
                        "step": step + 1,
                        "reasoning": reasoning,
                        "actions": [],
                        "status": "done"
                    })
                    break

                # Execute actions
                action_results = []
                for action in actions:
                    result_str = self._execute_action(action)
                    action_results.append({"action": action, "result": result_str})
                    print(f"  -> Executed: {result_str}")

                history.append({
                    "step": step + 1,
                    "reasoning": reasoning,
                    "actions": action_results,
                    "status": "in_progress"
                })

            except (KeyError, IndexError) as e:
                print(f"[Error] Failed to parse Gemini response: {e}")
                print(f"Raw response: {json.dumps(result, indent=2)[:500]}")
                break

        return {
            "task": task,
            "total_steps": len(history),
            "history": history,
            "final_screenshot": self._screenshot(),
        }

    def check_health(self) -> str:
        """Quick health check: screenshot + analyze."""
        self._init_browser()
        screenshot_b64 = self._screenshot()

        content = {
            "role": "user",
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": screenshot_b64,
                    }
                },
                {"text": "Analyze this NeverZero health dashboard. Is the system healthy? If there are issues, describe them and suggest what to click or do to fix them. Be concise."},
            ],
        }

        result = self._call_gemini([content])
        try:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text
        except (KeyError, IndexError):
            return json.dumps(result)


class SimulatedComputerUseAgent:
    """Simulated agent for testing without Gemini API or browser."""

    def __init__(self):
        self.call_count = 0

    def run_task(self, task: str, max_steps: int = 10) -> Dict[str, Any]:
        self.call_count += 1
        return {
            "task": task,
            "total_steps": 1,
            "history": [{
                "step": 1,
                "reasoning": "SIMULATION: Would analyze dashboard and execute UI actions via Playwright",
                "actions": [],
                "status": "done"
            }],
            "final_screenshot": "",
        }

    def check_health(self) -> str:
        self.call_count += 1
        if self.call_count % 3 == 0:
            return (
                "ALERT: Detected 47 failed auth events. "
                "The auth service URL may be misconfigured. "
                "SUGGESTED FIX: Click the 'Fix Auth' button on the dashboard."
            )
        return "HEALTHY"


class SimulatedPlaywrightAgent:
    """Simulated agent that pretends to use Playwright but doesn't actually open a browser."""

    def __init__(self):
        self.call_count = 0

    def run_task(self, task: str, max_steps: int = 10) -> Dict[str, Any]:
        self.call_count += 1
        return {
            "task": task,
            "total_steps": 3,
            "history": [
                {
                    "step": 1,
                    "reasoning": "Screenshot shows 47 auth errors. Need to click the Fix Auth button.",
                    "actions": [{"action": "click", "x": 640, "y": 400, "result": "clicked Fix Auth button"}],
                    "status": "in_progress"
                },
                {
                    "step": 2,
                    "reasoning": "Auth URL dialog appeared. Need to type the correct URL.",
                    "actions": [{"action": "type", "x": 640, "y": 350, "text": "https://pulse.ayushojha.com", "result": "typed URL"}],
                    "status": "in_progress"
                },
                {
                    "step": 3,
                    "reasoning": "Fixed applied. Screenshot confirms all errors cleared. DONE",
                    "actions": [],
                    "status": "done"
                }
            ],
            "final_screenshot": "",
        }

    def check_health(self) -> str:
        self.call_count += 1
        if self.call_count % 3 == 0:
            return "ALERT: 47 auth failures detected. Need to fix auth service URL."
        return "HEALTHY"
