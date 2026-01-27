#!/usr/bin/env python3
"""
BlackRoad Integration Health Check for Mobile (Pyto/Pythonista)

Checks the health of all configured integrations from iOS devices.
Compatible with Pyto and Pythonista on iOS.

Usage:
    python integration_health.py [service]
    service: all, cloudflare, salesforce, vercel, digitalocean, anthropic, github
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

# Try to import requests, fall back to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    import ssl
    HAS_REQUESTS = False

# Colors for terminal output (may not work in all iOS terminals)
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

# Status indicators
OK = f"{Colors.GREEN}[OK]{Colors.RESET}"
WARN = f"{Colors.YELLOW}[WARN]{Colors.RESET}"
FAIL = f"{Colors.RED}[FAIL]{Colors.RESET}"
SKIP = f"{Colors.CYAN}[SKIP]{Colors.RESET}"

# Timeout for HTTP requests
TIMEOUT = 10

# Environment variables
ENV = {
    "CLOUDFLARE_API_TOKEN": os.environ.get("CLOUDFLARE_API_TOKEN", ""),
    "SALESFORCE_ACCESS_TOKEN": os.environ.get("SALESFORCE_ACCESS_TOKEN", ""),
    "SALESFORCE_INSTANCE_URL": os.environ.get("SALESFORCE_INSTANCE_URL", ""),
    "VERCEL_TOKEN": os.environ.get("VERCEL_TOKEN", ""),
    "DIGITALOCEAN_TOKEN": os.environ.get("DIGITALOCEAN_TOKEN", ""),
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
    "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", ""),
}

# Results tracking
results: Dict[str, str] = {}


def http_get(url: str, headers: Dict[str, str] = None) -> Tuple[int, Optional[Dict]]:
    """Make HTTP GET request."""
    headers = headers or {}

    if HAS_REQUESTS:
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            try:
                body = response.json()
            except:
                body = {"text": response.text[:200]}
            return response.status_code, body
        except requests.exceptions.Timeout:
            return 0, {"error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return 0, {"error": "Connection failed"}
        except Exception as e:
            return 0, {"error": str(e)}
    else:
        try:
            req = urllib.request.Request(url)
            for key, value in headers.items():
                req.add_header(key, value)

            # Create SSL context that doesn't verify certificates (for iOS compatibility)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as response:
                body = json.loads(response.read().decode('utf-8'))
                return response.status, body
        except urllib.error.HTTPError as e:
            return e.code, {"error": str(e)}
        except urllib.error.URLError as e:
            return 0, {"error": str(e.reason)}
        except Exception as e:
            return 0, {"error": str(e)}


def check_endpoint(name: str, url: str, headers: Dict[str, str] = None,
                   expected_code: int = 200) -> bool:
    """Check if an endpoint is reachable and returns expected status."""
    if not url:
        print(f"  {SKIP} {name} (URL not configured)")
        results[name] = "skip"
        return True

    status, _ = http_get(url, headers)

    if status == expected_code:
        print(f"  {OK} {name} (HTTP {status})")
        results[name] = "ok"
        return True
    elif status == 0:
        print(f"  {FAIL} {name} (Connection failed)")
        results[name] = "fail"
        return False
    else:
        print(f"  {WARN} {name} (HTTP {status}, expected {expected_code})")
        results[name] = "warn"
        return False


def header(title: str) -> None:
    """Print section header."""
    print(f"\n{Colors.BLUE}{'─' * 50}{Colors.RESET}")
    print(f"{Colors.BLUE}  {title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 50}{Colors.RESET}")


def check_cloudflare() -> None:
    """Check Cloudflare integration."""
    header("Cloudflare")

    token = ENV["CLOUDFLARE_API_TOKEN"]
    if not token:
        print(f"  {SKIP} Cloudflare API (Token not configured)")
        results["cloudflare_api"] = "skip"
        return

    headers = {"Authorization": f"Bearer {token}"}
    check_endpoint(
        "Cloudflare API",
        "https://api.cloudflare.com/client/v4/user/tokens/verify",
        headers
    )

    # Check Cloudflare Pages site
    check_endpoint(
        "Cloudflare Pages",
        "https://blackroad-earth.pages.dev"
    )


def check_salesforce() -> None:
    """Check Salesforce integration."""
    header("Salesforce")

    token = ENV["SALESFORCE_ACCESS_TOKEN"]
    instance_url = ENV["SALESFORCE_INSTANCE_URL"]

    if not token or not instance_url:
        print(f"  {SKIP} Salesforce (Credentials not configured)")
        results["salesforce"] = "skip"
        return

    headers = {"Authorization": f"Bearer {token}"}
    check_endpoint(
        "Salesforce API",
        f"{instance_url}/services/data/v59.0",
        headers
    )


def check_vercel() -> None:
    """Check Vercel integration."""
    header("Vercel")

    token = ENV["VERCEL_TOKEN"]
    if not token:
        print(f"  {SKIP} Vercel API (Token not configured)")
        results["vercel"] = "skip"
        return

    headers = {"Authorization": f"Bearer {token}"}
    check_endpoint(
        "Vercel API",
        "https://api.vercel.com/v2/user",
        headers
    )


def check_digitalocean() -> None:
    """Check DigitalOcean integration."""
    header("DigitalOcean")

    token = ENV["DIGITALOCEAN_TOKEN"]
    if not token:
        print(f"  {SKIP} DigitalOcean API (Token not configured)")
        results["digitalocean"] = "skip"
        return

    headers = {"Authorization": f"Bearer {token}"}
    check_endpoint(
        "DigitalOcean API",
        "https://api.digitalocean.com/v2/account",
        headers
    )


def check_anthropic() -> None:
    """Check Anthropic/Claude integration."""
    header("Anthropic (Claude)")

    api_key = ENV["ANTHROPIC_API_KEY"]
    if not api_key:
        print(f"  {SKIP} Anthropic API (Key not configured)")
        results["anthropic"] = "skip"
        return

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    # Note: Anthropic doesn't have a simple health endpoint,
    # so we check if we can list models
    status, response = http_get("https://api.anthropic.com/v1/models", headers)

    if status == 200:
        print(f"  {OK} Anthropic API (Authenticated)")
        results["anthropic"] = "ok"
    elif status == 401:
        print(f"  {FAIL} Anthropic API (Invalid API key)")
        results["anthropic"] = "fail"
    else:
        print(f"  {WARN} Anthropic API (HTTP {status})")
        results["anthropic"] = "warn"


def check_github() -> None:
    """Check GitHub integration."""
    header("GitHub")

    # Check public API
    check_endpoint("GitHub API (Public)", "https://api.github.com")

    # Check authenticated API
    token = ENV["GITHUB_TOKEN"]
    if not token:
        print(f"  {SKIP} GitHub API (Authenticated) - Token not configured")
        results["github_auth"] = "skip"
        return

    headers = {"Authorization": f"Bearer {token}"}
    check_endpoint(
        "GitHub API (Authenticated)",
        "https://api.github.com/user",
        headers
    )


def check_local() -> None:
    """Check local state files."""
    header("Local State")

    state_file = ".kanban/state/current.json"
    if os.path.exists(state_file):
        print(f"  {OK} Kanban state file exists")
        results["state_file"] = "ok"

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            print(f"  {OK} Kanban state JSON valid")
            results["state_valid"] = "ok"

            # Print some stats
            stats = state.get("statistics", {})
            total = stats.get("total_cards", 0)
            print(f"  {Colors.CYAN}[INFO]{Colors.RESET} Total cards: {total}")
        except json.JSONDecodeError:
            print(f"  {FAIL} Kanban state JSON invalid")
            results["state_valid"] = "fail"
    else:
        print(f"  {FAIL} Kanban state file not found")
        results["state_file"] = "fail"


def print_summary() -> None:
    """Print summary of all checks."""
    header("Summary")

    ok = sum(1 for v in results.values() if v == "ok")
    warn = sum(1 for v in results.values() if v == "warn")
    fail = sum(1 for v in results.values() if v == "fail")
    skip = sum(1 for v in results.values() if v == "skip")
    total = len(results)

    print(f"\n  Total checks: {total}")
    print(f"  {Colors.GREEN}Passed:{Colors.RESET}  {ok}")
    print(f"  {Colors.YELLOW}Warning:{Colors.RESET} {warn}")
    print(f"  {Colors.RED}Failed:{Colors.RESET}  {fail}")
    print(f"  {Colors.CYAN}Skipped:{Colors.RESET} {skip}")

    print()
    if fail > 0:
        print(f"  {Colors.RED}Overall Status: UNHEALTHY{Colors.RESET}")
    elif warn > 0:
        print(f"  {Colors.YELLOW}Overall Status: DEGRADED{Colors.RESET}")
    else:
        print(f"  {Colors.GREEN}Overall Status: HEALTHY{Colors.RESET}")


def main(service: str = "all") -> None:
    """Main health check function."""
    print("╔" + "═" * 58 + "╗")
    print("║       BlackRoad Integration Health Check (Mobile)       ║")
    print(f"║       {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC                      ║")
    print("╚" + "═" * 58 + "╝")

    checks = {
        "local": check_local,
        "github": check_github,
        "cloudflare": check_cloudflare,
        "salesforce": check_salesforce,
        "vercel": check_vercel,
        "digitalocean": check_digitalocean,
        "anthropic": check_anthropic,
    }

    if service == "all":
        for check_func in checks.values():
            check_func()
    elif service in checks:
        checks[service]()
    else:
        print(f"Unknown service: {service}")
        print(f"Available: {', '.join(checks.keys())}, all")
        sys.exit(1)

    print_summary()

    # Exit with appropriate code
    has_failures = any(v == "fail" for v in results.values())
    sys.exit(1 if has_failures else 0)


if __name__ == "__main__":
    service = sys.argv[1] if len(sys.argv) > 1 else "all"
    main(service)
