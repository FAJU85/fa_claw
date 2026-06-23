
Summary: Deploy Open Claw to Hugging Face Space Pro using Northflank Infrastructure-as-Code template automation with multi-provider secret injection and persistent stateful storage

Description:
As a developer, I want to deploy the Open Claw headless engine to Hugging Face Space Pro via a fully automated Northflank IaC pipeline, so that the deployment is repeatable, free from manual configuration drift, and integrated with Telegram, Groq, OpenRouter, and Hugging Face endpoints through a single declarative blueprint.

Acceptance Criteria:

Template Configuration:

· northflank-template.json file created in project repository with correct schema (apiVersion: "v1")
· Template name set to openclaw-automated-deployment
· All four secret arguments defined: TELEGRAM_BOT_TOKEN, GROQ_API_KEY, OPENROUTER_API_KEY, HUGGINGFACE_API_KEY
· GIT_REPO_URL argument defined as string type pointing to repository containing the Dockerfile

Sequential Workflow Execution:

· Workflow provision-openclaw-pipeline configured as sequential type
· Node 1 (target-project): Project openclaw-headless-runtime provisioned in region europe-west
· Node 2 (secure-runtime-secrets): Secret group openclaw-multi-provider-credentials created with all five environment variables mapped from arguments (TELEGRAM_BOT_TOKEN, GROQ_API_KEY, OPENROUTER_API_KEY, HUGGINGFACE_API_KEY, HF_TOKEN)
· Secret group correctly references target-project.id via projectContext binding

Persistent Storage:

· Node 3 (stateful-storage-volume): Volume openclaw-state provisioned with 4GB capacity
· Volume access mode set to shared-read-write-once
· Volume correctly references target-project.id via projectContext binding

Worker Service Deployment:

· Node 4 (headless-daemon-worker): Service openclaw-gateway deployed as worker type
· Billing plan set to micro deployment tier
· Source configured as VCS type pulling from GIT_REPO_URL argument on main branch
· Build method set to dockerfile with path ./Dockerfile
· Instance count set to 1
· Volume stateful-storage-volume.id mounted at /data path inside container
· Service correctly references target-project.id via projectContext binding

Runtime Verification:

· Template uploads to Northflank Dashboard without schema validation errors
· Template execution completes all four nodes sequentially without failures
· Secret group populates all five environment variables correctly at runtime
· Persistent volume attaches and is writable at /data
· Worker daemon builds successfully from Dockerfile in referenced repository
· Worker daemon starts without errors and maintains running state
· Open Claw engine responds to requests through configured providers (Telegram, Groq, OpenRouter, Hugging Face)

Operational Integrity:

· No manual post-deployment configuration performed in Northflank UI (zero configuration drift)
· All downstream changes made via template argument updates or repository commits only
· Deployment is reproducible by re-running template with same arguments

Technical Notes:

· Sequential workflow type enforces dependency resolution: volume and secrets must complete validation before worker service initializes
· Template arguments use Northflank's native parameterized injection (${arguments.VARIABLE_NAME}) and node dependency chaining (${target-project.id}, ${stateful-storage-volume.id})
· HF_TOKEN duplicated from HUGGINGFACE_API_KEY argument to satisfy Hugging Face SDK convention
· Shared-read-write-once access mode ensures single-instance write safety with read capability
· Dockerfile must exist at repository root and be valid for multi-stage or single-stage builds
· Northflank region europe-west selected; adjust if latency or data residency requirements differ

Risks and Trade-offs (Documented):

· Slight initial pipeline synchronization latency due to sequential node execution ordering
· Manual UI hotfixes post-deployment will break template blueprint integrity and be ignored on future runs
· Template argument changes require full re-execution; no incremental patching supported

Out of Scope:

· Custom domain or DNS configuration
· CI/CD integration beyond Northflank native VCS source linking
· Auto-scaling beyond single instance
· Multi-region failover
· Monitoring, alerting, or logging dashboards
· Duration/timebox not defined

---

User Story Canvas

Field Detail
Role As a developer deploying Open Claw to production infrastructure
Action I want to provision the entire Open Claw runtime stack — project, secrets, persistent volume, and headless worker daemon — through a single declarative Northflank IaC template that chains dependencies sequentially and injects multi-provider API credentials at runtime
Benefit So that deployment is fully automated, repeatable, free from manual setup errors and configuration drift, and integrated with Telegram, Groq, OpenRouter, and Hugging Face endpoints from first launch


Sub-Task 1: Prepare Repository and Dockerfile

· Verify Dockerfile exists at repository root
· Confirm Dockerfile builds successfully locally before Northflank execution
· Ensure Dockerfile exposes required ports if applicable (worker type may not require port exposure)
· Include all necessary runtime dependencies for Open Claw (Python/Node/binary dependencies based on Open Claw implementation)
· Verify .dockerignore excludes unnecessary files to reduce build context size
· Confirm repository is accessible via the URL provided in GIT_REPO_URL argument (public or authenticated access configured in Northflank VCS integration)

Sub-Task 2: Create Northflank Template

· Navigate to Northflank Dashboard → Templates → Create Template
· Switch view toggle from Visual to Code
· Paste complete northflank-template.json payload
· Validate schema: no JSON syntax errors, all node IDs unique, all references resolvable
· Save template with name openclaw-automated-deployment
· Confirm template appears in templates list

Sub-Task 3: Configure Secret Arguments

· Gather production-ready values for:
  · TELEGRAM_BOT_TOKEN (from BotFather or Telegram API console)
  · GROQ_API_KEY (from Groq Console)
  · OPENROUTER_API_KEY (from OpenRouter dashboard)
  · HUGGINGFACE_API_KEY (from Hugging Face user access tokens)
· Verify each key has appropriate permissions/scopes for Open Claw operations
· Confirm keys are active and not expired or revoked
· Store keys securely outside repository (do not commit to Git)

Sub-Task 4: Execute Template Run

· Open saved template and click Run
· Fill all argument fields in the generated form:
  · Paste each secret into its corresponding field
  · Provide full Git repository URL (including https:// or git@ prefix)
· Click Execute
· Monitor sequential pipeline progress in Northflank dashboard:
  · Node 1: Project creation → confirm openclaw-headless-runtime appears
  · Node 2: Secret group creation → confirm all five environment variables populated
  · Node 3: Volume provisioning → confirm 4GB volume openclaw-state created
  · Node 4: Service build and deploy → confirm Dockerfile build logs show success, worker daemon starts

Sub-Task 5: Post-Deployment Verification

· Access worker service logs via Northflank dashboard
· Confirm Open Claw engine initializes without fatal errors
· Verify Telegram integration: send test message to bot, confirm response
· Verify Groq integration: trigger a Groq-dependent operation, confirm API call succeeds
· Verify OpenRouter integration: trigger an OpenRouter-dependent operation, confirm API call succeeds
· Verify Hugging Face integration: trigger an HF-dependent operation, confirm HF_TOKEN resolves correctly
· Verify persistent storage: write test data to /data, restart service, confirm data persists across restart
· Confirm all environment variables are injected and readable at runtime (spot-check via logs or diagnostic command if available)

Sub-Task 6: Drift Prevention and Documentation

· Document in team runbook: all configuration changes must go through template argument updates or repository commits — no manual UI hotfixes
· If environment variables change: update template arguments and re-run, or use Northflank secret group update API
· If code changes: push to configured branch (main), trigger rebuild via Northflank VCS integration or re-run template
· Tag template version in repository for traceability
· Document rollback procedure: re-run previous template version with previous arguments if available

---

Dependencies and Constraints

Dependency Chain (Sequential Enforcement):

```
target-project (Node 1)
    │
    ├──> secure-runtime-secrets (Node 2) ── requires project.id
    │
    ├──> stateful-storage-volume (Node 3) ── requires project.id
    │
    └──> headless-daemon-worker (Node 4) ── requires project.id, volume.id, secrets populated
```

· Node 2 and Node 3 can theoretically run in parallel (both depend only on Node 1), but sequential workflow type ensures ordered execution for deterministic state
· Node 4 must wait for both Node 2 and Node 3 to complete successfully before starting build

External Dependencies:

· Northflank account with template creation permissions
· Git repository accessible to Northflank VCS integration (public repo or connected private repo with deploy keys)
· All four API providers (Telegram, Groq, OpenRouter, Hugging Face) operational during verification
· Docker Hub or container registry accessible if Dockerfile uses external base images

---

Edge Cases and Error Handling

Scenario Expected Behavior
Template schema validation fails on upload Northflank rejects save; fix JSON syntax or schema errors before retry
Git repository URL is unreachable Build step fails at Node 4; verify URL, branch name, and access permissions
Dockerfile build fails (syntax error, missing dependency) Build step fails at Node 4; fix Dockerfile, push to repository, re-run template or trigger rebuild
Secret argument left blank during Run Northflank prompts for required field; cannot proceed until all arguments provided
API key is invalid or expired Worker starts but runtime calls to that provider fail; verify key in provider console, update secret group, restart service
Volume mount fails or /data not writable Worker may fail at startup or lose state; check volume node status, access mode, and mount path
Worker daemon crashes after deployment Check logs for crash cause; fix in code, push to repository, redeploy
Template re-run with same arguments Northflank should detect existing resources and perform idempotent update where supported; verify no duplicate resources created
Multiple simultaneous template runs Risk of resource conflict; avoid concurrent runs on same template with same project name

---

Definition of Done

· northflank-template.json validated and saved in Northflank
· All four secret arguments populated with production keys
· Template execution completes all four nodes with green status
· Project openclaw-headless-runtime visible in Northflank dashboard
· Secret group openclaw-multi-provider-credentials contains all five variables
· Volume openclaw-state (4GB) provisioned and attached
· Service openclaw-gateway running with 1 instance
· Worker logs show Open Claw initialization without fatal errors
· Telegram bot responds to test message
· Groq, OpenRouter, and Hugging Face integrations verified operational
· Data persists across service restart (volume test passed)
· No manual UI configuration drift introduced
· Runbook entry documented for future template-based updates

---

Estimation Reference (T-Shirt Sizing)

Sub-Task Effort
Prepare Repository and Dockerfile S (if Dockerfile exists and builds) / M (if Dockerfile needs creation or fixes)
Create Northflank Template XS (paste and save)
Configure Secret Arguments XS (gather and input keys)
Execute Template Run XS (click Run, fill form, execute)
Post-Deployment Verification M (multi-provider testing with debugging cycles)
Drift Prevention and Documentation S (write runbook entry)
Total S-M depending on Dockerfile readiness and integration debugging

---

Rollback Plan

1. Identify failing component (project, secret group, volume, or service)
2. If template still in valid state: fix arguments or repository code, re-run template
3. If rollback to previous state needed: manually delete affected resources in Northflank and re-run last known-good template version
4. If full teardown required: delete project openclaw-headless-runtime and all child resources, re-run template from clean state
5. Document root cause and resolution in team knowledge base