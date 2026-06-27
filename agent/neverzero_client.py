"""NeverZero API client for triggering fixes from the self-healer agent."""
import os
import requests
from typing import Optional

NEVERZERO_BASE_URL = os.getenv("NEVERZERO_BASE_URL", "http://localhost:3000")
NEVERZERO_API_KEY = os.getenv("NEVERZERO_API_KEY", "")


class NeverZeroClient:
    """Client to interact with the NeverZero platform API."""

    def __init__(self, base_url: str = NEVERZERO_BASE_URL, api_key: str = NEVERZERO_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def get_health(self) -> dict:
        """Fetch NeverZero health status."""
        try:
            resp = requests.get(f"{self.base_url}/api/health", headers=self.headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_recent_events(self, limit: int = 50) -> list:
        """Fetch recent events from the ledger."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/events?limit={limit}",
                headers=self.headers,
                timeout=5,
            )
            resp.raise_for_status()
            return resp.json().get("events", [])
        except Exception as e:
            return [{"error": str(e)}]

    def get_auth_stats(self) -> dict:
        """Fetch authentication statistics."""
        try:
            resp = requests.get(
                f"{self.base_url}/api/auth/stats",
                headers=self.headers,
                timeout=5,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def fix_auth_service_url(self, new_url: str) -> dict:
        """Update the auth service URL configuration."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/admin/config",
                headers=self.headers,
                json={"auth_service_url": new_url},
                timeout=5,
            )
            resp.raise_for_status()
            return {"ok": True, "message": f"Auth service URL updated to {new_url}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def clear_redis_cache(self, pattern: str = "*") -> dict:
        """Clear Redis cache to resolve stale data issues."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/admin/cache/clear",
                headers=self.headers,
                json={"pattern": pattern},
                timeout=5,
            )
            resp.raise_for_status()
            return {"ok": True, "message": f"Cache cleared for pattern: {pattern}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def trigger_compaction(self, feature_id: str) -> dict:
        """Trigger feature compaction for a specific feature."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/admin/compaction",
                headers=self.headers,
                json={"feature_id": feature_id},
                timeout=30,
            )
            resp.raise_for_status()
            return {"ok": True, "message": f"Compaction triggered for {feature_id}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
