"""Interactive health dashboard for the NeverZero Self-Healer demo.

Serves at http://localhost:8080. Includes clickable "Fix Auth" and
"Clear Cache" buttons that the Computer Use agent can interact with.
"""
import json
import random
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Global state
metrics = {
    "system_status": "healthy",
    "error_count": 0,
    "auth_failures": 0,
    "auth_service_url": "https://pulse.ayushojha.com",
    "redis_status": "connected",
    "spicedb_status": "connected",
    "last_event_time": time.time(),
    "events_per_minute": 42,
    "active_sessions": 7,
}


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/":
            self._serve_dashboard()
        elif self.path == "/api/metrics":
            self._serve_metrics()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/fix-auth":
            self._fix_auth()
        elif self.path == "/api/clear-cache":
            self._clear_cache()
        else:
            self.send_error(404)

    def _fix_auth(self):
        metrics["error_count"] = 0
        metrics["auth_failures"] = 0
        metrics["system_status"] = "healthy"
        metrics["last_event_time"] = time.time()
        print(f"[Dashboard] Auth fixed at {time.strftime('%H:%M:%S')}")
        self._json_response({"ok": True, "message": "Auth fixed"})

    def _clear_cache(self):
        metrics["last_event_time"] = time.time()
        print(f"[Dashboard] Cache cleared at {time.strftime('%H:%M:%S')}")
        self._json_response({"ok": True, "message": "Cache cleared"})

    def _json_response(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _serve_dashboard(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        # Randomly inject errors for demo purposes
        if random.random() < 0.3:
            metrics["error_count"] = random.randint(1, 50)
            metrics["auth_failures"] = random.randint(1, 20)
            metrics["system_status"] = "degraded"
        else:
            metrics["error_count"] = 0
            metrics["auth_failures"] = 0
            metrics["system_status"] = "healthy"

        metrics["last_event_time"] = time.time()

        status_color = "#22c55e" if metrics["system_status"] == "healthy" else "#ef4444"
        status_emoji = "✅" if metrics["system_status"] == "healthy" else "⚠️"

        # Show buttons only when there are issues
        show_buttons = metrics["error_count"] > 0 or metrics["auth_failures"] > 0

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>NeverZero Health Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; background: #0f172a; color: #e2e8f0; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .header h1 {{ color: #38bdf8; margin: 0; }}
        .header p {{ color: #94a3b8; margin-top: 8px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; }}
        .card h3 {{ margin: 0 0 12px 0; color: #94a3b8; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .card .value {{ font-size: 32px; font-weight: 700; margin: 0; }}
        .card .value.green {{ color: #22c55e; }}
        .card .value.red {{ color: #ef4444; }}
        .card .value.yellow {{ color: #f59e0b; }}
        .status-bar {{ background: #1e293b; border-radius: 12px; padding: 20px; max-width: 1200px; margin: 0 auto 20px auto; border: 1px solid #334155; display: flex; align-items: center; gap: 16px; justify-content: space-between; }}
        .status-left {{ display: flex; align-items: center; gap: 16px; }}
        .status-dot {{ width: 16px; height: 16px; border-radius: 50%; background: {status_color}; }}
        .status-text {{ font-size: 18px; font-weight: 600; }}
        .fix-buttons {{ display: flex; gap: 12px; {'display: none;' if not show_buttons else ''} }}
        .fix-btn {{ background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }}
        .fix-btn:hover {{ background: #2563eb; }}
        .fix-btn.secondary {{ background: #f59e0b; }}
        .fix-btn.secondary:hover {{ background: #d97706; }}
        .footer {{ text-align: center; margin-top: 40px; color: #64748b; font-size: 12px; }}
        .toast {{ position: fixed; bottom: 20px; right: 20px; background: #22c55e; color: white; padding: 12px 24px; border-radius: 8px; display: none; font-weight: 600; }}
    </style>
    <meta http-equiv="refresh" content="5">
</head>
<body>
    <div class="header">
        <h1>NeverZero Health Dashboard</h1>
        <p>Real-time platform monitoring · Self-Healing Enabled</p>
    </div>
    <div class="status-bar">
        <div class="status-left">
            <div class="status-dot"></div>
            <div class="status-text">{status_emoji} System Status: {metrics["system_status"].upper()}</div>
        </div>
        <div class="fix-buttons" id="fixButtons">
            <button class="fix-btn" id="fixAuthBtn" onclick="fixAuth()">🔧 Fix Auth</button>
            <button class="fix-btn secondary" id="clearCacheBtn" onclick="clearCache()">🧹 Clear Cache</button>
        </div>
    </div>
    <div class="grid">
        <div class="card">
            <h3>Error Events (5m)</h3>
            <p class="value {'red' if metrics['error_count'] > 0 else 'green'}">{metrics["error_count"]}</p>
        </div>
        <div class="card">
            <h3>Auth Failures</h3>
            <p class="value {'red' if metrics['auth_failures'] > 0 else 'green'}">{metrics["auth_failures"]}</p>
        </div>
        <div class="card">
            <h3>Events / Minute</h3>
            <p class="value green">{metrics["events_per_minute"]}</p>
        </div>
        <div class="card">
            <h3>Active Sessions</h3>
            <p class="value green">{metrics["active_sessions"]}</p>
        </div>
        <div class="card">
            <h3>Redis</h3>
            <p class="value green">{metrics["redis_status"].upper()}</p>
        </div>
        <div class="card">
            <h3>SpiceDB</h3>
            <p class="value green">{metrics["spicedb_status"].upper()}</p>
        </div>
        <div class="card">
            <h3>Auth Service URL</h3>
            <p class="value yellow">{metrics["auth_service_url"]}</p>
        </div>
        <div class="card">
            <h3>Last Event</h3>
            <p class="value green">{time.strftime('%H:%M:%S', time.localtime(metrics['last_event_time']))}</p>
        </div>
    </div>
    <div class="footer">
        Powered by NeverZero · Gemini 3.5 Flash Computer Use · Self-Healing Agent
    </div>
    <div class="toast" id="toast"></div>
    <script>
        function showToast(msg) {{
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.style.display = 'block';
            setTimeout(() => t.style.display = 'none', 3000);
        }}
        function fixAuth() {{
            fetch('/api/fix-auth', {{method: 'POST'}})
                .then(r => r.json())
                .then(d => {{ showToast(d.message); location.reload(); }})
                .catch(e => showToast('Error: ' + e));
        }}
        function clearCache() {{
            fetch('/api/clear-cache', {{method: 'POST'}})
                .then(r => r.json())
                .then(d => {{ showToast(d.message); location.reload(); }})
                .catch(e => showToast('Error: ' + e));
        }}
    </script>
</body>
</html>"""
        self.wfile.write(html.encode())

    def _serve_metrics(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(metrics).encode())


if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("localhost", port), DashboardHandler)
    print(f"[Dashboard] Serving at http://localhost:{port}")
    print("[Dashboard] Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Dashboard] Stopped.")
