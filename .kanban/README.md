# BlackRoad Kanban Project System

## Overview

This kanban system integrates with multiple services to provide a unified project management experience across all BlackRoad repositories. It functions like Salesforce within GitHub, using CRM and Cloudflare for state management while Git maintains the files.

## Architecture

```
                    +------------------+
                    |   GitHub Repo    |
                    |   (Source of     |
                    |    Truth)        |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v----+  +------v------+  +----v--------+
     |  Cloudflare |  |  Salesforce |  |   Claude    |
     |   (CDN +    |  |   (CRM +    |  |   (Agent    |
     |   State)    |  |   Pipeline) |  |   Assist)   |
     +-------------+  +-------------+  +-------------+
              |              |              |
     +--------v--------------v--------------v--------+
     |              State Sync Layer                 |
     |         (SHA-256 Integrity Checks)            |
     +-----------------------------------------------+
              |
     +--------v-----------------------------------------+
     |                 Edge Devices                     |
     | Raspberry Pi | Termius | iSH | Working Copy     |
     | Shellfish | Pyto | Mobile Apps                  |
     +--------------------------------------------------+
```

## Directory Structure

```
.kanban/
├── README.md                 # This file
├── config.json               # Main configuration
├── state/
│   ├── current.json          # Current project state
│   ├── history/              # State history with hashes
│   └── checkpoints/          # Rollback points
├── integrations/
│   ├── cloudflare.json       # Cloudflare Workers/KV config
│   ├── salesforce.json       # Salesforce CRM integration
│   ├── vercel.json           # Vercel deployment config
│   ├── digitalocean.json     # DO droplets/apps config
│   ├── claude.json           # Claude AI agent config
│   ├── termius.json          # Termius SSH config
│   ├── mobile-apps.json      # iSH, Shellfish, Working Copy, Pyto
│   └── endpoints.json        # All API endpoints registry
├── agents/
│   ├── instructions.md       # Agent instructions
│   ├── todos/                # Agent-specific TODOs
│   └── templates/            # Task templates
├── hashing/
│   ├── sha256.js             # SHA-256 implementation
│   └── sha-infinity.js       # Recursive/chained hashing
└── workflows/
    ├── pr-validation.yml     # PR quality gates
    └── kanban-sync.yml       # State synchronization
```

## Quick Start

1. **Configure Secrets** - Add required API tokens to GitHub Secrets
2. **Initialize State** - Run the state initialization workflow
3. **Connect Services** - Verify all integrations are connected
4. **Start Tracking** - Create cards and track progress

## SHA-Infinity Hashing

The SHA-Infinity system provides cryptographic integrity for all state changes:

```javascript
// Chain depth determines security level
// sha-infinity(data, depth) = sha256(sha256(...sha256(data)...))
```

## Agent Instructions

See `.kanban/agents/instructions.md` for detailed agent operation guidelines.

## Support

- Email: blackroad.systems@gmail.com
- Website: https://blackroad.io
