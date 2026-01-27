#!/bin/bash
#
# BlackRoad Integration Health Check Script
# Checks the health of all configured integrations
#
# Usage: ./scripts/health-check.sh [service]
#   service: all, cloudflare, salesforce, vercel, digitalocean, claude, pi (default: all)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Status indicators
OK="${GREEN}[OK]${NC}"
WARN="${YELLOW}[WARN]${NC}"
FAIL="${RED}[FAIL]${NC}"
SKIP="${CYAN}[SKIP]${NC}"

# Timeout for HTTP requests (seconds)
TIMEOUT=10

# Results tracking
declare -A RESULTS

# Log functions
log() { echo -e "$1"; }
header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    if [ -z "$url" ]; then
        echo -e "  $SKIP $name (URL not configured)"
        RESULTS[$name]="skip"
        return 0
    fi

    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected_code" ]; then
        echo -e "  $OK $name (HTTP $response)"
        RESULTS[$name]="ok"
    elif [ "$response" = "000" ]; then
        echo -e "  $FAIL $name (Connection failed)"
        RESULTS[$name]="fail"
    else
        echo -e "  $WARN $name (HTTP $response, expected $expected_code)"
        RESULTS[$name]="warn"
    fi
}

# Check if host is reachable
check_host() {
    local name=$1
    local host=$2

    if [ -z "$host" ]; then
        echo -e "  $SKIP $name (Host not configured)"
        RESULTS[$name]="skip"
        return 0
    fi

    if ping -c 1 -W 2 "$host" &> /dev/null; then
        echo -e "  $OK $name ($host reachable)"
        RESULTS[$name]="ok"
    else
        echo -e "  $FAIL $name ($host unreachable)"
        RESULTS[$name]="fail"
    fi
}

# Check API with authentication
check_api_auth() {
    local name=$1
    local url=$2
    local token_var=$3

    local token="${!token_var}"

    if [ -z "$token" ]; then
        echo -e "  $SKIP $name (Token not configured: $token_var)"
        RESULTS[$name]="skip"
        return 0
    fi

    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT \
        -H "Authorization: Bearer $token" \
        "$url" 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "  $OK $name (Authenticated)"
        RESULTS[$name]="ok"
    elif [ "$response" = "401" ] || [ "$response" = "403" ]; then
        echo -e "  $FAIL $name (Auth failed: HTTP $response)"
        RESULTS[$name]="fail"
    elif [ "$response" = "000" ]; then
        echo -e "  $FAIL $name (Connection failed)"
        RESULTS[$name]="fail"
    else
        echo -e "  $WARN $name (HTTP $response)"
        RESULTS[$name]="warn"
    fi
}

# Cloudflare checks
check_cloudflare() {
    header "Cloudflare"

    check_api_auth "Cloudflare API" \
        "https://api.cloudflare.com/client/v4/user/tokens/verify" \
        "CLOUDFLARE_API_TOKEN"

    check_endpoint "Cloudflare Pages (blackroad-earth)" \
        "https://blackroad-earth.pages.dev" \
        "200"
}

# Salesforce checks
check_salesforce() {
    header "Salesforce"

    if [ -z "$SALESFORCE_INSTANCE_URL" ]; then
        echo -e "  $SKIP Salesforce (Instance URL not configured)"
        RESULTS["salesforce"]="skip"
    else
        check_endpoint "Salesforce Instance" \
            "$SALESFORCE_INSTANCE_URL/services/data" \
            "200"
    fi
}

# Vercel checks
check_vercel() {
    header "Vercel"

    check_api_auth "Vercel API" \
        "https://api.vercel.com/v2/user" \
        "VERCEL_TOKEN"
}

# DigitalOcean checks
check_digitalocean() {
    header "DigitalOcean"

    check_api_auth "DigitalOcean API" \
        "https://api.digitalocean.com/v2/account" \
        "DIGITALOCEAN_TOKEN"
}

# Claude/Anthropic checks
check_claude() {
    header "Claude (Anthropic)"

    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo -e "  $SKIP Anthropic API (Key not configured)"
        RESULTS["anthropic"]="skip"
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT \
            -H "x-api-key: $ANTHROPIC_API_KEY" \
            -H "anthropic-version: 2023-06-01" \
            "https://api.anthropic.com/v1/models" 2>/dev/null || echo "000")

        if [ "$response" = "200" ]; then
            echo -e "  $OK Anthropic API (Authenticated)"
            RESULTS["anthropic"]="ok"
        else
            echo -e "  $WARN Anthropic API (HTTP $response)"
            RESULTS["anthropic"]="warn"
        fi
    fi
}

# Pi Cluster checks
check_pi() {
    header "Raspberry Pi Cluster"

    check_host "Pi Master" "${PI_MASTER_HOST:-pi-master.local}"
    check_host "Pi Worker 1" "${PI_WORKER_1_HOST:-pi-worker-1.local}"
    check_host "Pi Worker 2" "${PI_WORKER_2_HOST:-pi-worker-2.local}"
    check_host "Pi Storage" "${PI_STORAGE_HOST:-pi-storage.local}"
}

# GitHub checks
check_github() {
    header "GitHub"

    check_endpoint "GitHub API" \
        "https://api.github.com" \
        "200"

    check_api_auth "GitHub Auth" \
        "https://api.github.com/user" \
        "GITHUB_TOKEN"
}

# Local state checks
check_local() {
    header "Local State"

    if [ -f "$ROOT_DIR/.kanban/state/current.json" ]; then
        echo -e "  $OK Kanban state file exists"
        RESULTS["state_file"]="ok"

        # Validate JSON
        if cat "$ROOT_DIR/.kanban/state/current.json" | python3 -m json.tool > /dev/null 2>&1; then
            echo -e "  $OK Kanban state JSON valid"
            RESULTS["state_valid"]="ok"
        else
            echo -e "  $FAIL Kanban state JSON invalid"
            RESULTS["state_valid"]="fail"
        fi
    else
        echo -e "  $FAIL Kanban state file missing"
        RESULTS["state_file"]="fail"
    fi

    # Check hashing modules
    if [ -f "$ROOT_DIR/.kanban/hashing/sha256.js" ]; then
        echo -e "  $OK SHA-256 module exists"
        RESULTS["sha256"]="ok"
    else
        echo -e "  $WARN SHA-256 module missing"
        RESULTS["sha256"]="warn"
    fi

    if [ -f "$ROOT_DIR/.kanban/hashing/sha-infinity.js" ]; then
        echo -e "  $OK SHA-Infinity module exists"
        RESULTS["sha_infinity"]="ok"
    else
        echo -e "  $WARN SHA-Infinity module missing"
        RESULTS["sha_infinity"]="warn"
    fi
}

# Print summary
print_summary() {
    header "Summary"

    local ok=0
    local warn=0
    local fail=0
    local skip=0

    for key in "${!RESULTS[@]}"; do
        case "${RESULTS[$key]}" in
            ok) ((ok++)) ;;
            warn) ((warn++)) ;;
            fail) ((fail++)) ;;
            skip) ((skip++)) ;;
        esac
    done

    local total=$((ok + warn + fail + skip))

    echo ""
    echo -e "  Total checks: $total"
    echo -e "  ${GREEN}Passed:${NC}  $ok"
    echo -e "  ${YELLOW}Warning:${NC} $warn"
    echo -e "  ${RED}Failed:${NC}  $fail"
    echo -e "  ${CYAN}Skipped:${NC} $skip"
    echo ""

    if [ $fail -gt 0 ]; then
        echo -e "  ${RED}Overall Status: UNHEALTHY${NC}"
        return 1
    elif [ $warn -gt 0 ]; then
        echo -e "  ${YELLOW}Overall Status: DEGRADED${NC}"
        return 0
    else
        echo -e "  ${GREEN}Overall Status: HEALTHY${NC}"
        return 0
    fi
}

# Main function
main() {
    local service="${1:-all}"

    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║       BlackRoad Integration Health Check               ║"
    echo "║       $(date '+%Y-%m-%d %H:%M:%S %Z')                        ║"
    echo "╚════════════════════════════════════════════════════════╝"

    case "$service" in
        all)
            check_local
            check_github
            check_cloudflare
            check_salesforce
            check_vercel
            check_digitalocean
            check_claude
            check_pi
            ;;
        cloudflare) check_cloudflare ;;
        salesforce) check_salesforce ;;
        vercel) check_vercel ;;
        digitalocean) check_digitalocean ;;
        claude) check_claude ;;
        pi) check_pi ;;
        github) check_github ;;
        local) check_local ;;
        *)
            echo "Unknown service: $service"
            echo "Usage: $0 [all|cloudflare|salesforce|vercel|digitalocean|claude|pi|github|local]"
            exit 1
            ;;
    esac

    print_summary
}

main "$@"
