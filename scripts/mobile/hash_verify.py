#!/usr/bin/env python3
"""
BlackRoad Hash Verification Script for Mobile (Pyto/Pythonista)

Verifies SHA-256 and SHA-Infinity hashes for state integrity.
Compatible with Pyto and Pythonista on iOS.

Usage:
    python hash_verify.py [state_file]
"""

import json
import hashlib
import sys
import os
from datetime import datetime
from typing import Dict, Any, Tuple

# Default paths
DEFAULT_STATE_FILE = ".kanban/state/current.json"
SHA_INFINITY_DEFAULT_DEPTH = 7


def sha256(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def sha_infinity(data: str, depth: int = 7, include_depth: bool = True) -> str:
    """
    Compute SHA-Infinity hash (recursive SHA-256).

    SHA-Infinity applies SHA-256 multiple times based on depth,
    creating a computationally expensive but highly secure hash.

    Formula: sha-infinity(data, depth) = sha256(sha256(...sha256(data)...))

    Args:
        data: The data to hash
        depth: Number of hash iterations (default: 7)
        include_depth: Whether to include depth in final hash

    Returns:
        The SHA-Infinity hash
    """
    salt = "blackroad-infinity"

    # Initial hash with salt
    current_hash = sha256(f"{salt}:{data}")

    # Recursive hashing
    for i in range(1, depth):
        current_hash = sha256(current_hash)

    # Optionally include depth in final hash for verification
    if include_depth:
        current_hash = sha256(f"{current_hash}:depth:{depth}")

    return current_hash


def stable_json(obj: Any) -> str:
    """
    Create stable JSON string with sorted keys.
    Ensures consistent hashing regardless of key order.
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return json.dumps(obj)

    if isinstance(obj, list):
        return '[' + ','.join(stable_json(item) for item in obj) + ']'

    if isinstance(obj, dict):
        sorted_items = sorted(obj.items())
        pairs = [f'{json.dumps(k)}:{stable_json(v)}' for k, v in sorted_items]
        return '{' + ','.join(pairs) + '}'

    return json.dumps(obj)


def load_state(file_path: str) -> Dict[str, Any]:
    """Load state from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: State file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)


def compute_hashes(data: str, depth: int = 7) -> Dict[str, str]:
    """Compute both SHA-256 and SHA-Infinity hashes."""
    return {
        "sha256": sha256(data),
        "sha_infinity": sha_infinity(data, depth),
        "chain_depth": depth
    }


def verify_integrity(state: Dict[str, Any],
                    expected_integrity: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify state integrity against expected hashes.

    Args:
        state: The state object to verify
        expected_integrity: Expected hash values

    Returns:
        Tuple of (is_valid, details)
    """
    # Remove integrity from state for hashing (if present)
    state_for_hash = {k: v for k, v in state.items() if k != 'integrity'}
    state_json = stable_json(state_for_hash)

    depth = expected_integrity.get("chain_depth", SHA_INFINITY_DEFAULT_DEPTH)
    computed = compute_hashes(state_json, depth)

    sha256_valid = computed["sha256"] == expected_integrity.get("sha256", "")
    infinity_valid = computed["sha_infinity"] == expected_integrity.get("sha_infinity", "")

    return (sha256_valid and infinity_valid), {
        "sha256": {
            "expected": expected_integrity.get("sha256", "not_provided"),
            "computed": computed["sha256"],
            "valid": sha256_valid
        },
        "sha_infinity": {
            "expected": expected_integrity.get("sha_infinity", "not_provided"),
            "computed": computed["sha_infinity"],
            "valid": infinity_valid,
            "depth": depth
        },
        "overall_valid": sha256_valid and infinity_valid
    }


def print_hash_details(label: str, expected: str, computed: str, valid: bool) -> None:
    """Print formatted hash comparison."""
    status = "VALID" if valid else "INVALID"
    status_color = "\033[92m" if valid else "\033[91m"  # Green or Red
    reset = "\033[0m"

    print(f"\n{label}:")
    print(f"  Expected: {expected[:32]}..." if len(expected) > 32 else f"  Expected: {expected}")
    print(f"  Computed: {computed[:32]}..." if len(computed) > 32 else f"  Computed: {computed}")
    print(f"  Status:   {status_color}{status}{reset}")


def main(state_file: str = DEFAULT_STATE_FILE) -> None:
    """Main verification function."""
    print("=" * 60)
    print("  BlackRoad Hash Verification")
    print(f"  {datetime.utcnow().isoformat()}Z")
    print("=" * 60)

    # Load state
    print(f"\n[Loading] {state_file}")
    state = load_state(state_file)

    # Get expected integrity if present
    expected_integrity = state.get("metadata", {}).get("integrity", {})

    if not expected_integrity:
        print("\n[Warning] No integrity record found in state")
        print("[Info] Computing fresh hashes...")

        state_for_hash = {k: v for k, v in state.items() if k != 'integrity'}
        state_json = stable_json(state_for_hash)
        hashes = compute_hashes(state_json, SHA_INFINITY_DEFAULT_DEPTH)

        print(f"\n[SHA-256]")
        print(f"  Hash: {hashes['sha256']}")

        print(f"\n[SHA-Infinity] (depth: {hashes['chain_depth']})")
        print(f"  Hash: {hashes['sha_infinity']}")

        print("\n" + "=" * 60)
        print("  No existing integrity to verify against")
        print("  Use computed hashes for future verification")
        print("=" * 60)
        return

    # Verify integrity
    print("\n[Verifying] Checking state integrity...")
    is_valid, details = verify_integrity(state, expected_integrity)

    # Print results
    print_hash_details(
        "SHA-256",
        details["sha256"]["expected"],
        details["sha256"]["computed"],
        details["sha256"]["valid"]
    )

    print_hash_details(
        f"SHA-Infinity (depth: {details['sha_infinity']['depth']})",
        details["sha_infinity"]["expected"],
        details["sha_infinity"]["computed"],
        details["sha_infinity"]["valid"]
    )

    # Summary
    print("\n" + "=" * 60)
    if is_valid:
        print("  \033[92mINTEGRITY VERIFIED\033[0m")
        print("  State is authentic and unmodified")
    else:
        print("  \033[91mINTEGRITY CHECK FAILED\033[0m")
        print("  State may have been modified or corrupted")
        print("\n  Recommended actions:")
        print("  1. Restore from last known good backup")
        print("  2. Investigate source of modification")
        print("  3. Re-sync from primary source (GitHub)")
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STATE_FILE
    main(file_path)
