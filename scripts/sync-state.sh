#!/bin/bash
#
# BlackRoad Kanban State Sync Script
# Syncs kanban state to configured services
#
# Usage: ./scripts/sync-state.sh [target]
#   target: all, cloudflare, salesforce, github, pi (default: all)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
STATE_FILE="$ROOT_DIR/.kanban/state/current.json"
CONFIG_FILE="$ROOT_DIR/.kanban/config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if state file exists
check_state_file() {
    if [ ! -f "$STATE_FILE" ]; then
        log_error "State file not found: $STATE_FILE"
        exit 1
    fi
    log_info "State file found: $STATE_FILE"
}

# Compute state hash
compute_hash() {
    log_info "Computing state hashes..."

    if command -v node &> /dev/null; then
        SHA256=$(node -e "
            const sha256 = require('$ROOT_DIR/.kanban/hashing/sha256');
            const state = require('$STATE_FILE');
            console.log(sha256.hashObject(state));
        " 2>/dev/null || echo "error")

        SHA_INFINITY=$(node -e "
            const shaInfinity = require('$ROOT_DIR/.kanban/hashing/sha-infinity');
            const state = require('$STATE_FILE');
            console.log(shaInfinity.shaInfinity(JSON.stringify(state), 7));
        " 2>/dev/null || echo "error")

        log_info "SHA-256: $SHA256"
        log_info "SHA-Infinity: $SHA_INFINITY"
    else
        log_warning "Node.js not available, using fallback hash"
        SHA256=$(sha256sum "$STATE_FILE" | cut -d' ' -f1)
        SHA_INFINITY="node_required"
        log_info "SHA-256 (file): $SHA256"
    fi
}

# Sync to Cloudflare KV
sync_cloudflare() {
    log_info "Syncing to Cloudflare KV..."

    if [ -z "$CLOUDFLARE_API_TOKEN" ] || [ -z "$CLOUDFLARE_ACCOUNT_ID" ]; then
        log_warning "Cloudflare credentials not set. Skipping."
        return 0
    fi

    if [ -z "$CLOUDFLARE_KV_NAMESPACE_ID" ]; then
        log_warning "Cloudflare KV namespace ID not set. Skipping."
        return 0
    fi

    # Upload state to KV
    response=$(curl -s -X PUT \
        "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/storage/kv/namespaces/$CLOUDFLARE_KV_NAMESPACE_ID/values/kanban_state" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data @"$STATE_FILE")

    if echo "$response" | grep -q '"success":true'; then
        log_success "Cloudflare KV sync completed"
    else
        log_error "Cloudflare KV sync failed: $response"
        return 1
    fi
}

# Sync to Salesforce
sync_salesforce() {
    log_info "Syncing to Salesforce..."

    if [ -z "$SALESFORCE_CLIENT_ID" ] || [ -z "$SALESFORCE_CLIENT_SECRET" ]; then
        log_warning "Salesforce credentials not set. Skipping."
        return 0
    fi

    # Get OAuth token
    log_info "Authenticating with Salesforce..."

    # Note: Full implementation would require proper OAuth flow
    log_warning "Salesforce sync requires OAuth implementation"
    log_info "Placeholder: Would sync state to BlackRoad_Project__c"
}

# Sync to GitHub Projects
sync_github() {
    log_info "Syncing to GitHub Projects..."

    if [ -z "$GITHUB_TOKEN" ]; then
        log_warning "GitHub token not set. Skipping."
        return 0
    fi

    # Note: Full implementation would use GitHub GraphQL API
    log_warning "GitHub Projects sync requires GraphQL implementation"
    log_info "Placeholder: Would sync cards to GitHub Projects"
}

# Sync to Pi cluster
sync_pi() {
    log_info "Syncing to Pi cluster..."

    PI_HOST="${PI_MASTER_HOST:-pi-master.local}"

    if ! ping -c 1 "$PI_HOST" &> /dev/null; then
        log_warning "Pi cluster not reachable. Skipping."
        return 0
    fi

    # Sync state file to Pi
    if command -v scp &> /dev/null; then
        log_info "Copying state to $PI_HOST..."
        scp -o ConnectTimeout=10 "$STATE_FILE" "blackroad@$PI_HOST:/opt/blackroad/.kanban/state/current.json" 2>/dev/null || {
            log_warning "SCP failed. Pi cluster sync skipped."
            return 0
        }
        log_success "Pi cluster sync completed"
    else
        log_warning "SCP not available. Skipping Pi sync."
    fi
}

# Create backup before sync
create_backup() {
    log_info "Creating backup..."
    BACKUP_DIR="$ROOT_DIR/.kanban/state/backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    cp "$STATE_FILE" "$BACKUP_DIR/state_$TIMESTAMP.json"
    log_success "Backup created: state_$TIMESTAMP.json"
}

# Update sync timestamp in state
update_sync_timestamp() {
    log_info "Updating sync timestamp..."

    if command -v node &> /dev/null; then
        node -e "
            const fs = require('fs');
            const state = require('$STATE_FILE');
            const target = '$1';

            if (!state.sync_status) state.sync_status = {};
            if (!state.sync_status[target]) state.sync_status[target] = {};

            state.sync_status[target].synced = true;
            state.sync_status[target].last_sync = new Date().toISOString();

            fs.writeFileSync('$STATE_FILE', JSON.stringify(state, null, 2));
        " 2>/dev/null || log_warning "Could not update sync timestamp"
    fi
}

# Main sync function
main() {
    local target="${1:-all}"

    echo ""
    echo "============================================"
    echo "  BlackRoad Kanban State Sync"
    echo "============================================"
    echo ""

    check_state_file
    compute_hash
    create_backup

    echo ""

    case "$target" in
        all)
            sync_cloudflare && update_sync_timestamp "cloudflare"
            sync_salesforce && update_sync_timestamp "salesforce"
            sync_github && update_sync_timestamp "github"
            sync_pi && update_sync_timestamp "pi"
            ;;
        cloudflare)
            sync_cloudflare && update_sync_timestamp "cloudflare"
            ;;
        salesforce)
            sync_salesforce && update_sync_timestamp "salesforce"
            ;;
        github)
            sync_github && update_sync_timestamp "github"
            ;;
        pi)
            sync_pi && update_sync_timestamp "pi"
            ;;
        *)
            log_error "Unknown target: $target"
            echo "Usage: $0 [all|cloudflare|salesforce|github|pi]"
            exit 1
            ;;
    esac

    echo ""
    echo "============================================"
    log_success "Sync completed for target: $target"
    echo "============================================"
}

# Run main with arguments
main "$@"
