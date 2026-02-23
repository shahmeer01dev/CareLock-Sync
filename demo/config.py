"""
config.py — CareLock Sync Demo
Shared configuration, API keys, colour helpers, and request wrapper.
Import from here in every demo script.
"""

import sys
import textwrap
import time
from typing import Any, Optional

import requests

# ── Connection ────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"
TIMEOUT  = 30

# ── API Keys ──────────────────────────────────────────────────────────────────
ADMIN_KEY    = "clk-admin-change-me-in-prod"
CGH_KEY      = "clk-cgh001-hospital-key"
PGH_KEY      = "clk-pgh002-hospital-key"
READONLY_KEY = "clk-readonly-analytics-key"
BAD_KEY      = "hacker-key-99999"

# ── ANSI colours (auto-off when not a TTY) ────────────────────────────────────
_USE_COLOUR = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOUR else text

def green(t):  return _c("32;1", t)
def red(t):    return _c("31;1", t)
def yellow(t): return _c("33;1", t)
def cyan(t):   return _c("36;1", t)
def bold(t):   return _c("1",    t)
def dim(t):    return _c("2",    t)

# ── Formatting helpers ────────────────────────────────────────────────────────
def section(title: str) -> None:
    bar = "=" * 62
    print(f"\n{bar}")
    print(f"  {title.upper()}")
    print(f"{bar}\n")

def row(label: str, value: Any, width: int = 26, ok: bool = True) -> None:
    colour = green if ok else red
    print(f"  {label.ljust(width)} {colour(str(value))}")

def divider(char: str = "-", width: int = 62) -> None:
    print(f"  {char * width}")

# ── Request wrapper ───────────────────────────────────────────────────────────
class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail      = detail
        super().__init__(f"HTTP {status_code}: {detail}")


def call(
    method:         str,
    path:           str,
    api_key:        Optional[str] = None,
    body:           Optional[dict] = None,
    expect:         int  = 200,
    raise_on_error: bool = True,
) -> tuple:
    """
    Execute one HTTP request.
    Returns (status_code, response_dict, elapsed_ms).
    Never prints raw JSON. Raises APIError or exits on connection failure.
    """
    url     = BASE_URL + path
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        t0       = time.perf_counter()
        response = requests.request(method.upper(), url, headers=headers,
                                    json=body, timeout=TIMEOUT)
        elapsed  = round((time.perf_counter() - t0) * 1000)
    except requests.ConnectionError:
        print(red(f"\n  ERROR: Cannot reach {BASE_URL}"))
        print(dim("  Start the server: uvicorn api.main:app --port 8000"))
        sys.exit(1)
    except requests.Timeout:
        print(red(f"\n  ERROR: Request timed out after {TIMEOUT}s"))
        sys.exit(1)

    try:
        data = response.json()
    except Exception:
        data = {"raw": response.text}

    if raise_on_error and response.status_code != expect:
        detail = data.get("detail", response.text[:200]) if isinstance(data, dict) else response.text[:200]
        raise APIError(response.status_code, detail)

    return response.status_code, data, elapsed
