# Open Claw Automated Deployment

This repository contains the Infrastructure-as-Code (IaC) template and deployment files for deploying the Open Claw headless engine to Hugging Face Space Pro using Northflank.

## Overview

This deployment automates the provisioning of:
- **Project**: `openclaw-headless-runtime` in europe-west region
- **Secrets**: Multi-provider API credentials (Telegram, Groq, OpenRouter, Hugging Face)
- **Storage**: 4GB persistent volume mounted at `/data`
- **Service**: Worker daemon pulling from this repository

## Files

- `northflank-template.json` - Northflank IaC template with sequential workflow
- `Dockerfile` - Container build instructions for the Open Claw daemon
- `requirements.txt` - Python dependencies
- `main.py` - Main entry point for the headless daemon
- `.dockerignore` - Excludes unnecessary files from Docker build context

## Prerequisites

1. Northflank account with template creation permissions
2. Git repository accessible to Northflank VCS integration
3. API keys from:
   - Telegram BotFather (`OPENCLAW_TELEGRAM_BOT_TOKEN`)
   - Groq Console (`OPENCLAW_GROQ_API_KEY`)
   - OpenRouter Dashboard (`OPENCLAW_OPENROUTER_API_KEY`)
   - Hugging Face User Settings (`OPENCLAW_HUGGINGFACE_API_KEY`)

## Deployment Steps

### 1. Upload Template to Northflank

1. Navigate to Northflank Dashboard → Templates → Create Template
2. Switch view toggle from Visual to Code
3. Paste the contents of `northflank-template.json`
4. Save template with name `openclaw-automated-deployment`

### 2. Execute Template

1. Open the saved template and click **Run**
2. Fill in all argument fields:
   - `OPENCLAW_TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `OPENCLAW_GROQ_API_KEY`: Your Groq API key
   - `OPENCLAW_OPENROUTER_API_KEY`: Your OpenRouter API key
   - `OPENCLAW_HUGGINGFACE_API_KEY`: Your Hugging Face API key
   - `GIT_REPO_URL`: URL to this Git repository
3. Click **Execute**

### 3. Monitor Deployment

The sequential workflow will execute:
1. **Node 1**: Create project `openclaw-headless-runtime`
2. **Node 2**: Create secret group with all API credentials
3. **Node 3**: Provision 4GB persistent volume
4. **Node 4**: Build and deploy worker service

### 4. Verify Deployment

- Check worker service logs in Northflank dashboard
- Verify Open Claw initializes without errors
- Test integrations:
  - Send a message to your Telegram bot
  - Trigger Groq-dependent operations
  - Trigger OpenRouter-dependent operations
  - Trigger Hugging Face-dependent operations
- Verify persistent storage by writing/reading data at `/data`

## Architecture

```
target-project (Node 1)
    │
    ├──> secure-runtime-secrets (Node 2) ── requires project.id
    │
    ├──> stateful-storage-volume (Node 3) ── requires project.id
    │
    └──> headless-daemon-worker (Node 4) ── requires project.id, volume.id, secrets
```

## Configuration

### Environment Variables

The following environment variables are injected at runtime via the secret group:

| Variable | Description |
|----------|-------------|
| `OPENCLAW_TELEGRAM_BOT_TOKEN` | Telegram Bot authentication token |
| `OPENCLAW_GROQ_API_KEY` | Groq LLM inference API key |
| `OPENCLAW_OPENROUTER_API_KEY` | OpenRouter multi-model API key |
| `OPENCLAW_HUGGINGFACE_API_KEY` | Hugging Face model access key |
| `OPENCLAW_HF_TOKEN` | Alias for OPENCLAW_HUGGINGFACE_API_KEY (HF SDK convention) |

### Persistent Storage

- **Volume Name**: `openclaw-state`
- **Capacity**: 4GB
- **Access Mode**: `shared-read-write-once`
- **Mount Path**: `/data`

## Updating Configuration

### To Change API Keys
Update template arguments and re-run the template.

### To Change Application Code
Push changes to the `main` branch. Northflank will automatically trigger a rebuild via VCS integration.

### To Change Infrastructure
Modify `northflank-template.json`, commit to repository, and re-run the template.

## Drift Prevention

**Important**: All configuration changes must go through:
1. Template argument updates (for secrets/configuration)
2. Repository commits (for code changes)

**Do not** make manual changes in the Northflank UI, as this will cause configuration drift and break template reproducibility.

## Rollback

If deployment fails:
1. Identify the failing component in Northflank dashboard
2. Fix the issue (update arguments or push code fixes)
3. Re-run the template
4. If needed, manually delete affected resources and re-run from clean state

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Template validation fails | Check JSON syntax and schema compliance |
| Git repository unreachable | Verify URL, branch name, and access permissions |
| Dockerfile build fails | Check Dockerfile syntax and dependencies |
| API calls fail at runtime | Verify API keys are valid and have correct permissions |
| Volume mount fails | Check volume status and access mode |
| Worker crashes | Review logs for error details |

## License

[Add your license information here]
