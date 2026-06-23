# Open Claw Automated Deployment

This repository contains the Infrastructure-as-Code (IaC) template and deployment files for deploying the Open Claw headless engine to Hugging Face Space Pro using Northflank.

## Overview

This deployment automates the provisioning of:
- **Project**: `openclaw-headless-runtime` in europe-west region
- **Secrets**: API credentials (Telegram, Hugging Face)
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
   - Hugging Face User Settings (`OPENCLAW_HUGGINGFACE_API_KEY`)

**Note**: Groq and OpenRouter API keys are optional and can be added later when needed.

## Deployment Steps

### 1. Upload Template to Northflank

1. Navigate to Northflank Dashboard → Templates → Create Template
2. Switch view toggle from Visual to Code
3. Paste the contents of `northflank-template.json`
4. Save template with name `openclaw-automated-deployment`

### 2. Execute Template

1. Open the saved template and click **Run**
2. Fill in the argument fields:
   - `OPENCLAW_TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `OPENCLAW_HUGGINGFACE_API_KEY`: Your Hugging Face token (must have the **Inference Providers** permission)
   - `GIT_REPO_URL`: HTTPS URL to this Git repository
   - `GIT_BRANCH`: Branch to build from (default `main`)
   - `PROJECT_REGION`: Northflank region (default `europe-west`)
   - `DEPLOYMENT_PLAN`: Northflank compute plan ID for the running worker (default `nf-compute-20`)
   - `BUILD_PLAN`: Northflank compute plan ID used for the image build (default `nf-compute-400-16`)
3. Click **Execute**

> **Plan IDs**: Northflank templates require the *plan ID* (e.g. `nf-compute-20`),
> not the friendly name shown in the UI. Pick valid compute plans for your
> account and pass them via `DEPLOYMENT_PLAN` (runtime) and `BUILD_PLAN` (build).

### 3. Monitor Deployment

The sequential workflow will execute:
1. **Project** (`openclaw-headless-runtime`) is created.
2. **SecretGroup** (`openclaw-credentials`) is created with the API credentials. It is
   restricted to workloads carrying the `openclaw` tag, so its variables are injected
   only into the tagged service (not every workload in the project). Tag-based
   restriction is used instead of a service-`id` reference so it resolves correctly
   regardless of node ordering.
3. **CombinedService** (`openclaw-gateway`) builds the Dockerfile from the repo and
   deploys it. It exposes no ports, so it runs as a long-lived worker (the Telegram
   bot uses outbound long-polling).
4. **Volume** (`openclaw-state`, 4GB) is provisioned and attached to the service at `/data`.

### 4. Verify Deployment

- Check worker service logs in Northflank dashboard
- Verify Open Claw initializes without errors
- Test integrations:
  - Send a message to your Telegram bot
  - Trigger Hugging Face-dependent operations
- Verify persistent storage by writing/reading data at `/data`

## Architecture

```
project (openclaw-headless-runtime)
    │   (child workflow runs in projectId context)
    │
    ├──> SecretGroup (openclaw-credentials)   — restricted to the `openclaw` tag, injects into the tagged service
    │
    ├──> CombinedService (openclaw-gateway)   — builds Dockerfile, deploys portless worker
    │
    └──> Volume (openclaw-state, 4GB)         — attached to ${refs.service.id} at /data
```

## Configuration

### Environment Variables

The following environment variables are injected at runtime via the secret group:

| Variable | Description |
|----------|-------------|
| `OPENCLAW_TELEGRAM_BOT_TOKEN` | Telegram Bot authentication token (**required**) |
| `OPENCLAW_GROQ_API_KEY` | Groq API key. When set, Groq is the **preferred** AI provider |
| `OPENCLAW_HUGGINGFACE_API_KEY` | Hugging Face token (used when Groq is not configured) |
| `OPENCLAW_HF_TOKEN` | Alias for OPENCLAW_HUGGINGFACE_API_KEY (HF SDK convention) |

**Provider selection**: if `OPENCLAW_GROQ_API_KEY` is set the bot uses Groq;
otherwise it falls back to Hugging Face. If neither is set, messages get a
placeholder reply. At least one provider key is needed for AI responses.

**Optional Environment Variables** (can be added later):

| Variable | Description |
|----------|-------------|
| `OPENCLAW_GROQ_MODEL` | Groq chat-completion model id (default: `llama-3.3-70b-versatile`) |
| `OPENCLAW_HF_MODEL` | HF Inference Providers chat model id (default: `Qwen/Qwen2.5-7B-Instruct`) |
| `OPENCLAW_OPENROUTER_API_KEY` | OpenRouter multi-model API key (not yet wired up) |

> **Note**: The Hugging Face token must be a user access token with the
> **"Inference Providers"** permission. Open Claw calls the chat-completions
> API through the `router.huggingface.co` endpoint (the legacy
> `api-inference.huggingface.co` serverless endpoint is no longer used).

### Persistent Storage

- **Volume Name**: `openclaw-state`
- **Capacity**: 4GB (`storageSize: 4096` MB)
- **Storage Class**: `ssd`
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
| API calls fail at runtime | Verify API keys (Telegram, Hugging Face) are valid and have correct permissions |
| Volume mount fails | Check volume status and access mode |
| Worker crashes | Review logs for error details |

## License

[Add your license information here]
