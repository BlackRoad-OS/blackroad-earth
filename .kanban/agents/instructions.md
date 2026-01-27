# BlackRoad Agent Instructions

## Overview

This document provides comprehensive instructions for AI agents working within the BlackRoad ecosystem. All agents must follow these guidelines to ensure consistency, quality, and successful integration across the million+ repositories.

## Core Principles

### 1. State Integrity First
- **ALWAYS** verify SHA-256/SHA-Infinity hashes before and after state changes
- **NEVER** commit or push without verifying state integrity
- **ALWAYS** update kanban cards when starting/completing work

### 2. No Failed PRs
The primary goal is **zero failed pull requests**. Follow this checklist:

- [ ] Read the kanban card fully before starting
- [ ] Verify branch is up-to-date with main
- [ ] Run all tests locally before pushing
- [ ] Verify state hashes match
- [ ] Link PR to kanban card
- [ ] Request review from appropriate agents/humans

### 3. Cross-Service Synchronization
State must be synchronized across:
- GitHub (source of truth for code)
- Cloudflare KV (edge state cache)
- Salesforce (CRM and pipeline tracking)
- Local Pi cluster (on-premise state)

---

## Agent Types & Responsibilities

### Kanban Manager Agent
**Model**: Claude Sonnet 4
**Purpose**: Manage kanban board state and card movements

**Responsibilities**:
1. Create new cards for incoming tasks
2. Move cards between columns based on status
3. Assign priority and labels
4. Notify relevant agents of assignments
5. Track WIP limits and block violations

**Commands**:
```bash
# Create a new card
kanban create --title "Task title" --priority high --label feature

# Move a card
kanban move --card-id card_001 --to in_progress

# Assign a card
kanban assign --card-id card_001 --to @claude-agent
```

### Code Review Agent
**Model**: Claude Opus 4.5
**Purpose**: Review pull requests and provide feedback

**Checklist**:
- [ ] Code follows project style guidelines
- [ ] No security vulnerabilities (OWASP Top 10)
- [ ] No hardcoded secrets or credentials
- [ ] Tests cover new functionality
- [ ] Documentation updated if needed
- [ ] Performance considerations addressed
- [ ] State hash verification passes

**Review Template**:
```markdown
## Code Review Summary

### Overview
[Brief description of changes]

### Security Check
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] No hardcoded credentials
- [ ] Input validation present

### Quality Check
- [ ] Code is readable and maintainable
- [ ] Functions are appropriately sized
- [ ] Error handling is adequate
- [ ] Tests are comprehensive

### State Integrity
- [ ] SHA-256 hash verified: `{hash}`
- [ ] SHA-Infinity hash verified: `{hash}`

### Recommendation
[APPROVE / REQUEST_CHANGES / COMMENT]
```

### PR Validator Agent
**Model**: Claude Sonnet 4
**Purpose**: Validate PRs against kanban requirements

**Validation Steps**:
1. Verify PR is linked to a kanban card
2. Verify card is in correct column (should be "Review")
3. Verify all commits have valid hashes
4. Verify tests pass
5. Verify no WIP limit violations
6. Update card status on merge

### Integration Monitor Agent
**Model**: Claude 3.5 Haiku
**Purpose**: Monitor health of all integrations

**Monitoring Checklist**:
- Cloudflare Workers responding
- Salesforce API accessible
- Vercel deployments healthy
- DigitalOcean droplets running
- Pi cluster nodes online
- All webhooks functional

**Alert Levels**:
- `INFO`: Normal operations
- `WARNING`: Degraded performance
- `ERROR`: Service unavailable
- `CRITICAL`: Multiple services down

### Deployment Coordinator Agent
**Model**: Claude Sonnet 4
**Purpose**: Coordinate deployments across platforms

**Deployment Checklist**:
```markdown
## Pre-Deployment
- [ ] All tests passing
- [ ] State integrity verified
- [ ] Kanban card in "Testing" or "Done"
- [ ] No blocking issues
- [ ] Rollback plan documented

## Deployment
- [ ] Deploy to staging first
- [ ] Verify staging health
- [ ] Deploy to production
- [ ] Verify production health
- [ ] Update monitoring

## Post-Deployment
- [ ] Notify stakeholders
- [ ] Update kanban card
- [ ] Sync state to all services
- [ ] Close related issues
```

---

## Standard Operating Procedures

### Starting a New Task

1. **Check the Kanban Board**
   ```bash
   # View current board state
   cat .kanban/state/current.json | jq '.boards.main'
   ```

2. **Claim a Card**
   - Move card to "In Progress"
   - Assign yourself
   - Verify WIP limits not exceeded

3. **Create Feature Branch**
   ```bash
   git checkout -b claude/feature-name-{session_id}
   ```

4. **Update State Hash**
   ```javascript
   const { createStateIntegrity } = require('./.kanban/hashing/sha-infinity');
   const state = require('./.kanban/state/current.json');
   const integrity = createStateIntegrity(state);
   console.log('New integrity:', integrity);
   ```

### Completing a Task

1. **Run Tests**
   ```bash
   # Run all tests
   npm test

   # Verify no security issues
   npm audit
   ```

2. **Verify State Integrity**
   ```javascript
   const { verifyStateIntegrity } = require('./.kanban/hashing/sha-infinity');
   const result = verifyStateIntegrity(currentState, integrityRecord);
   if (!result.valid) {
       throw new Error('State integrity check failed');
   }
   ```

3. **Create Pull Request**
   ```bash
   gh pr create \
     --title "feat: Description of changes" \
     --body "## Summary
   - Change 1
   - Change 2

   ## Linked Card
   Closes #card_id

   ## State Integrity
   SHA-256: {hash}
   SHA-Infinity: {hash}

   ## Test Plan
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed"
   ```

4. **Move Card to Review**
   - Update card status
   - Link PR to card
   - Request review

### Handling Failures

**If Tests Fail**:
1. Do NOT push to main
2. Create a fix commit
3. Re-run tests
4. Update card with notes

**If State Integrity Fails**:
1. Do NOT proceed with any changes
2. Restore from last known good state
3. Investigate cause of mismatch
4. Report to Integration Monitor

**If Deployment Fails**:
1. Trigger immediate rollback
2. Alert all relevant agents
3. Create incident card
4. Investigate root cause

---

## Hash Verification Protocol

### When to Verify

| Action | SHA-256 | SHA-Infinity |
|--------|---------|--------------|
| Read state | Yes | No |
| Write state | Yes | Yes |
| Before commit | Yes | Yes |
| Before deploy | Yes | Yes |
| After deploy | Yes | Yes |
| Sync between services | Yes | Yes |

### Verification Code

```javascript
const sha256 = require('./.kanban/hashing/sha256');
const shaInfinity = require('./.kanban/hashing/sha-infinity');

// Quick verification (SHA-256 only)
function quickVerify(data, hash) {
    return sha256.verifyHash(JSON.stringify(data), hash);
}

// Full verification (SHA-256 + SHA-Infinity)
function fullVerify(data, integrity) {
    const result = shaInfinity.verifyStateIntegrity(data, integrity);
    return result.valid;
}

// Always use full verification for:
// - Deployments
// - State syncs
// - Critical updates
```

---

## Communication Protocols

### Agent-to-Agent
- Use structured JSON messages
- Include sender agent ID
- Include timestamp
- Include relevant hashes

### Agent-to-Human
- Use clear, concise language
- Summarize actions taken
- Highlight any issues
- Provide next steps

### Notifications

```javascript
const notification = {
    type: 'TASK_COMPLETED',
    agent: 'code-reviewer',
    task_id: 'card_001',
    summary: 'Completed code review for PR #42',
    result: 'APPROVED',
    hash: '{sha256_hash}',
    timestamp: Date.now()
};
```

---

## Error Handling

### Error Categories

1. **Recoverable**: Retry with backoff
2. **Transient**: Wait and retry once
3. **Permanent**: Escalate to human
4. **Critical**: Stop all operations, alert everyone

### Retry Strategy

```javascript
const retryConfig = {
    maxRetries: 3,
    initialDelayMs: 1000,
    backoffMultiplier: 2,
    maxDelayMs: 30000
};

async function withRetry(operation, config = retryConfig) {
    let lastError;
    let delay = config.initialDelayMs;

    for (let i = 0; i < config.maxRetries; i++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error;
            await sleep(delay);
            delay = Math.min(delay * config.backoffMultiplier, config.maxDelayMs);
        }
    }

    throw lastError;
}
```

---

## Security Guidelines

### Secrets Management
- NEVER commit secrets to git
- Use environment variables
- Reference secrets by env var name in configs
- Verify no secrets in diffs before committing

### Access Control
- Use least privilege principle
- Verify permissions before operations
- Log all privileged actions
- Rotate credentials regularly

### Audit Trail
- Log all state changes
- Include hash in every log entry
- Retain logs for compliance
- Enable real-time monitoring

---

## Quick Reference

### Common Commands

```bash
# Check kanban state
cat .kanban/state/current.json | jq .

# Verify current state hash
node -e "
const sha = require('./.kanban/hashing/sha-infinity');
const state = require('./.kanban/state/current.json');
console.log(sha.createStateIntegrity(state));
"

# Sync state to Cloudflare
./scripts/sync-state.sh cloudflare

# Check all integrations
./scripts/health-check.sh

# Run PR validation
./scripts/validate-pr.sh
```

### Important Paths

```
.kanban/
├── config.json          # Main configuration
├── state/current.json   # Current state (source of truth)
├── integrations/        # Service configurations
├── hashing/             # Hash implementations
├── agents/              # Agent configs and instructions
└── workflows/           # GitHub Actions workflows
```

---

## Support

- **Email**: blackroad.systems@gmail.com
- **Website**: https://blackroad.io
- **Issues**: GitHub Issues on respective repositories

Remember: **The goal is ZERO failed PRs.** When in doubt, verify hashes, check state, and ask for help.
