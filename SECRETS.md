# Required Secrets Configuration

This document lists all the secrets/environment variables required for the BlackRoad Kanban system integrations.

## GitHub Repository Secrets

Add these secrets to your GitHub repository settings (`Settings > Secrets and variables > Actions`):

### Cloudflare

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token with Pages and KV permissions | Yes |
| `CLOUDFLARE_ACCOUNT_ID` | Your Cloudflare account ID | Yes |
| `CLOUDFLARE_ZONE_ID` | Zone ID for your domain (optional) | No |
| `CLOUDFLARE_KV_NAMESPACE_ID` | KV namespace ID for kanban state | No |

### Salesforce

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `SALESFORCE_CLIENT_ID` | Connected App Client ID | For SF sync |
| `SALESFORCE_CLIENT_SECRET` | Connected App Client Secret | For SF sync |
| `SALESFORCE_USERNAME` | Salesforce username | For SF sync |
| `SALESFORCE_PASSWORD` | Salesforce password | For SF sync |
| `SALESFORCE_SECURITY_TOKEN` | Salesforce security token | For SF sync |
| `SALESFORCE_INSTANCE_URL` | Instance URL (e.g., https://na1.salesforce.com) | For SF sync |

### Vercel

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `VERCEL_TOKEN` | Vercel API token | For Vercel deploy |
| `VERCEL_TEAM_ID` | Vercel team ID (if using teams) | No |
| `VERCEL_ORG_ID` | Vercel organization ID | No |

### DigitalOcean

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `DIGITALOCEAN_TOKEN` | DigitalOcean API token | For DO infra |
| `DIGITALOCEAN_SPACES_ACCESS_KEY` | Spaces access key | For DO Spaces |
| `DIGITALOCEAN_SPACES_SECRET_KEY` | Spaces secret key | For DO Spaces |

### Anthropic (Claude)

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key | For Claude agents |
| `ANTHROPIC_ORG_ID` | Organization ID (if applicable) | No |

### Termius

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `TERMIUS_API_KEY` | Termius API key for host sync | For Termius |
| `TERMIUS_TEAM_ID` | Termius team ID | No |

### Raspberry Pi Cluster

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `PI_MASTER_HOST` | IP/hostname of Pi master node | For Pi cluster |
| `PI_WORKER_1_HOST` | IP/hostname of Pi worker 1 | For Pi cluster |
| `PI_WORKER_2_HOST` | IP/hostname of Pi worker 2 | For Pi cluster |
| `PI_STORAGE_HOST` | IP/hostname of Pi storage node | For Pi cluster |
| `PI_SSH_KEY` | SSH private key for Pi access (base64) | For Pi cluster |

### Notifications

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `SLACK_WEBHOOK` | Slack webhook URL for notifications | No |
| `DISCORD_WEBHOOK` | Discord webhook URL for notifications | No |

### MinIO (Pi Cluster Storage)

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `MINIO_ACCESS_KEY` | MinIO access key | For Pi storage |
| `MINIO_SECRET_KEY` | MinIO secret key | For Pi storage |

### Tailscale (VPN)

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `TAILSCALE_AUTH_KEY` | Tailscale auth key for nodes | For VPN |

### Cloudflare Tunnel

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `CF_TUNNEL_ID` | Cloudflare Tunnel ID | For CF Tunnel |
| `CF_TUNNEL_CREDENTIALS` | Tunnel credentials JSON | For CF Tunnel |

---

## Local Development (.env)

For local development, create a `.env` file (never commit this!):

```bash
# .env - DO NOT COMMIT

# Cloudflare
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id

# Salesforce
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_security_token
SALESFORCE_INSTANCE_URL=https://yourinstance.salesforce.com

# Vercel
VERCEL_TOKEN=your_vercel_token

# DigitalOcean
DIGITALOCEAN_TOKEN=your_do_token

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key

# GitHub
GITHUB_TOKEN=your_github_token

# Pi Cluster
PI_MASTER_HOST=192.168.1.100
PI_WORKER_1_HOST=192.168.1.101
PI_WORKER_2_HOST=192.168.1.102
PI_STORAGE_HOST=192.168.1.103
```

---

## Mobile App Configuration

### Pyto / Pythonista

Set environment variables in the app settings or use a local config file:

```python
# config_local.py - DO NOT COMMIT
import os

os.environ["CLOUDFLARE_API_TOKEN"] = "your_token"
os.environ["ANTHROPIC_API_KEY"] = "your_key"
# ... etc
```

### Working Copy

Configure SSH keys in Working Copy for Git operations.

### Termius / Shellfish

Import SSH keys and host configurations through the app's secure storage.

---

## Security Best Practices

1. **Never commit secrets** - Always use environment variables or secret managers
2. **Rotate regularly** - Rotate API keys and tokens periodically
3. **Least privilege** - Only grant necessary permissions to each token
4. **Audit access** - Regularly review who has access to secrets
5. **Use short-lived tokens** - Where possible, use tokens that expire
6. **Monitor usage** - Set up alerts for unusual API usage patterns

---

## Token Permissions Reference

### Cloudflare API Token Permissions

Required permissions:
- `Account.Cloudflare Pages` - Edit
- `Account.Workers KV Storage` - Edit
- `Account.Workers R2 Storage` - Edit (if using R2)
- `Zone.DNS` - Edit (if managing DNS)

### GitHub Token Scopes

Required scopes:
- `repo` - Full control of private repositories
- `workflow` - Update GitHub Action workflows
- `write:packages` - Upload packages (if needed)
- `admin:repo_hook` - Manage webhooks

### Vercel Token

Create from Vercel dashboard with appropriate team access.

### DigitalOcean Token

Create with Read/Write access for required resources.

---

## Verification

Run the health check to verify your configuration:

```bash
./scripts/health-check.sh
```

Or from mobile:

```bash
python scripts/mobile/integration_health.py
```
