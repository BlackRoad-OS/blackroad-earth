#!/usr/bin/env python3
"""
BlackRoad Kanban Sync Script for Mobile (Pyto/Pythonista)

Syncs kanban state across services from iOS devices.
Compatible with Pyto and Pythonista on iOS.

Usage:
    python kanban_sync.py [target]
    target: all, cloudflare, salesforce, github (default: all)
"""

import json
import hashlib
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Try to import requests, fall back to urllib if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False

# Configuration
CONFIG = {
    "state_file": ".kanban/state/current.json",
    "config_file": ".kanban/config.json",
    "backup_dir": ".kanban/state/backups",
    "sha_infinity_depth": 7,
}

# Environment variables (set these in your environment or Pyto settings)
ENV_VARS = {
    "CLOUDFLARE_API_TOKEN": os.environ.get("CLOUDFLARE_API_TOKEN", ""),
    "CLOUDFLARE_ACCOUNT_ID": os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
    "CLOUDFLARE_KV_NAMESPACE_ID": os.environ.get("CLOUDFLARE_KV_NAMESPACE_ID", ""),
    "SALESFORCE_ACCESS_TOKEN": os.environ.get("SALESFORCE_ACCESS_TOKEN", ""),
    "SALESFORCE_INSTANCE_URL": os.environ.get("SALESFORCE_INSTANCE_URL", ""),
    "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", ""),
}


def sha256(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def sha_infinity(data: str, depth: int = 7) -> str:
    """
    Compute SHA-Infinity hash (recursive SHA-256).

    Args:
        data: The data to hash
        depth: Number of hash iterations

    Returns:
        The SHA-Infinity hash
    """
    salt = "blackroad-infinity"
    current_hash = sha256(f"{salt}:{data}")

    for _ in range(1, depth):
        current_hash = sha256(current_hash)

    # Include depth in final hash
    current_hash = sha256(f"{current_hash}:depth:{depth}")

    return current_hash


def stable_json(obj: Any) -> str:
    """Create stable JSON string with sorted keys."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def load_state() -> Dict[str, Any]:
    """Load current kanban state from file."""
    try:
        with open(CONFIG["state_file"], 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: State file not found: {CONFIG['state_file']}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in state file: {e}")
        sys.exit(1)


def save_state(state: Dict[str, Any]) -> None:
    """Save kanban state to file."""
    with open(CONFIG["state_file"], 'w') as f:
        json.dump(state, f, indent=2)


def create_backup(state: Dict[str, Any]) -> str:
    """Create a backup of the current state."""
    os.makedirs(CONFIG["backup_dir"], exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(CONFIG["backup_dir"], f"state_{timestamp}.json")

    with open(backup_file, 'w') as f:
        json.dump(state, f, indent=2)

    return backup_file


def compute_integrity(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compute integrity hashes for state."""
    state_json = stable_json(state)
    depth = CONFIG["sha_infinity_depth"]

    return {
        "sha256": sha256(state_json),
        "sha_infinity": sha_infinity(state_json, depth),
        "chain_depth": depth,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "algorithm": "sha-infinity-v1"
    }


def http_request(method: str, url: str, headers: Dict[str, str],
                 data: Optional[Dict] = None) -> tuple:
    """Make HTTP request, compatible with both requests and urllib."""
    if HAS_REQUESTS:
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                return 400, {"error": f"Unsupported method: {method}"}

            return response.status_code, response.json() if response.text else {}
        except Exception as e:
            return 0, {"error": str(e)}
    else:
        # Fallback to urllib
        try:
            req = urllib.request.Request(url, method=method)
            for key, value in headers.items():
                req.add_header(key, value)

            if data:
                req.data = json.dumps(data).encode('utf-8')
                req.add_header('Content-Type', 'application/json')

            with urllib.request.urlopen(req, timeout=30) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return e.code, {"error": str(e)}
        except Exception as e:
            return 0, {"error": str(e)}


def sync_cloudflare(state: Dict[str, Any], integrity: Dict[str, Any]) -> bool:
    """Sync state to Cloudflare KV."""
    print("\n[Cloudflare] Syncing to Cloudflare KV...")

    token = ENV_VARS["CLOUDFLARE_API_TOKEN"]
    account_id = ENV_VARS["CLOUDFLARE_ACCOUNT_ID"]
    namespace_id = ENV_VARS["CLOUDFLARE_KV_NAMESPACE_ID"]

    if not all([token, account_id, namespace_id]):
        print("[Cloudflare] Credentials not configured. Skipping.")
        return True

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/storage/kv/namespaces/{namespace_id}/values/kanban_state"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Add integrity to state for storage
    state_with_integrity = {**state, "integrity": integrity}

    status, response = http_request("PUT", url, headers, state_with_integrity)

    if status == 200 and response.get("success"):
        print("[Cloudflare] Sync successful!")
        return True
    else:
        print(f"[Cloudflare] Sync failed: {response}")
        return False


def sync_salesforce(state: Dict[str, Any], integrity: Dict[str, Any]) -> bool:
    """Sync state to Salesforce."""
    print("\n[Salesforce] Syncing to Salesforce...")

    token = ENV_VARS["SALESFORCE_ACCESS_TOKEN"]
    instance_url = ENV_VARS["SALESFORCE_INSTANCE_URL"]

    if not all([token, instance_url]):
        print("[Salesforce] Credentials not configured. Skipping.")
        return True

    # This would update the BlackRoad_Project__c record
    url = f"{instance_url}/services/data/v59.0/sobjects/BlackRoad_Project__c"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "Kanban_State_Hash__c": integrity["sha256"],
        "Last_Sync__c": integrity["timestamp"],
        "Active_Cards__c": state.get("statistics", {}).get("total_cards", 0)
    }

    print("[Salesforce] Placeholder - would update BlackRoad_Project__c")
    print(f"[Salesforce] Payload: {json.dumps(payload, indent=2)}")

    return True


def sync_github(state: Dict[str, Any], integrity: Dict[str, Any]) -> bool:
    """Sync state to GitHub (update repository variable or dispatch event)."""
    print("\n[GitHub] Syncing to GitHub...")

    token = ENV_VARS["GITHUB_TOKEN"]

    if not token:
        print("[GitHub] Token not configured. Skipping.")
        return True

    # Dispatch a repository dispatch event to trigger sync workflow
    url = "https://api.github.com/repos/BlackRoad-OS/blackroad-earth/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    payload = {
        "event_type": "kanban_sync",
        "client_payload": {
            "sha256": integrity["sha256"],
            "sha_infinity": integrity["sha_infinity"],
            "timestamp": integrity["timestamp"],
            "source": "mobile_sync"
        }
    }

    status, response = http_request("POST", url, headers, payload)

    if status == 204 or status == 200:
        print("[GitHub] Dispatch event sent successfully!")
        return True
    else:
        print(f"[GitHub] Dispatch failed: {status} - {response}")
        return False


def main(target: str = "all") -> None:
    """Main sync function."""
    print("=" * 60)
    print("  BlackRoad Kanban Mobile Sync")
    print(f"  {datetime.utcnow().isoformat()}Z")
    print("=" * 60)

    # Load state
    print("\n[State] Loading kanban state...")
    state = load_state()
    print(f"[State] Loaded {state.get('statistics', {}).get('total_cards', 0)} cards")

    # Create backup
    print("\n[Backup] Creating backup...")
    backup_file = create_backup(state)
    print(f"[Backup] Created: {backup_file}")

    # Compute integrity
    print("\n[Hash] Computing integrity hashes...")
    integrity = compute_integrity(state)
    print(f"[Hash] SHA-256: {integrity['sha256'][:16]}...")
    print(f"[Hash] SHA-Infinity (depth {integrity['chain_depth']}): {integrity['sha_infinity'][:16]}...")

    # Sync to targets
    results = {}

    if target in ["all", "cloudflare"]:
        results["cloudflare"] = sync_cloudflare(state, integrity)

    if target in ["all", "salesforce"]:
        results["salesforce"] = sync_salesforce(state, integrity)

    if target in ["all", "github"]:
        results["github"] = sync_github(state, integrity)

    # Update state with sync status
    if "sync_status" not in state:
        state["sync_status"] = {}

    for service, success in results.items():
        if service not in state["sync_status"]:
            state["sync_status"][service] = {}
        state["sync_status"][service]["synced"] = success
        state["sync_status"][service]["last_sync"] = integrity["timestamp"]

    save_state(state)

    # Print summary
    print("\n" + "=" * 60)
    print("  Sync Summary")
    print("=" * 60)
    for service, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"  {service}: {status}")
    print("=" * 60)

    # Return exit code
    all_success = all(results.values())
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    main(target)
