# Progressive Deploy — grow the AWS stack step by step

Parent index: [`../README.md`](../README.md)  
Agent Runtime lab (required first): [`../02.strands-agentcore-bedrock`](../02.strands-agentcore-bedrock/)  
Companion lab (same app, one CDK app with stage flags instead of folders): [`../05.agentcore-production-deploy`](../05.agentcore-production-deploy/)

Each folder is a **complete, runnable snapshot**. Code only grows; nothing is removed between steps.

You deploy folder `01`, prove it works, open folder `02` beside it to see what changed, deploy `02` (same CloudFormation stack grows), and continue through `10`. Steps `11`–`13` are optional ops / alternate-compute add-ons after the full app works.

```
01_empty_cdk          → deploy
02_cognito_pool       → 01 + Cognito pool
03_cognito_client     → 02 + SPA client
04_demo_user          → 03 + demo user
05_s3_ui_bucket       → 04 + S3
06_cloudfront         → 05 + CloudFront placeholder
07_react_login        → 06 + React login (chat off)
08_apprunner_health   → 07 + FastAPI /health
09_jwt_lock           → 08 + JWT /api/me
10_agentcore_chat     → 09 + AgentCore chat (full)

# Optional — after the app works
11_ops_cicd           → 10 + App Runner autoscaling + budget + GitHub OIDC deploy role
12_fargate_alternative → same app on ECS Fargate + ALB (separate stack)
13_fargate_ops_cicd   → 12 + Fargate autoscaling + budget + GitHub OIDC deploy role
```

---

## What you are building

```
Browser (React)
    │  Cognito login → ID token (JWT)
    ▼
CloudFront (HTTPS)
    ├── static UI from private S3
    └── /api/*, /health → App Runner (FastAPI)
              │  IAM
              ▼
         AgentCore Runtime (Strands support agent)
```

**One sentence:** The browser never holds AWS keys. Cognito proves *who you are*. FastAPI uses *IAM* to call AgentCore. These folders show that path in AWS, one layer at a time.

---

## How to learn with these folders

1. Open `01_empty_cdk` and `02_cognito_pool` side-by-side in your IDE.
2. Deploy folder 01: `bash deploy.sh`
3. Read the delta in folder 02 (`cdk/stack.py` and `WHAT_CHANGED.md`).
4. Deploy folder 02 (updates the **same** stack).
5. Repeat through 10. Then optionally deploy `11_ops_cicd` (same stack), or the Fargate track (`12` → `13`, separate stack).

**Detailed walkthrough (why + how + verify):**  
[`STEP_BY_STEP.md`](./STEP_BY_STEP.md) — covers steps 01→10.

**Commands for your own stack name:**  
[`DEPLOY_YOUR_OWN_STACK.md`](./DEPLOY_YOUR_OWN_STACK.md)

```bash
export STACK_NAME=LaukiSupportClassA   # new name = new stack; omit for LaukiSupportStack
cd 06.progressive-deploy/01_empty_cdk && bash deploy.sh
cd ../02_cognito_pool && bash deploy.sh
# ...
export SUPPORT_RUNTIME_ARN='arn:aws:bedrock-agentcore:us-east-1:YOUR_ACCOUNT:runtime/...'
cd ../10_agentcore_chat && bash deploy.sh
# optional ops day (updates LaukiSupportStack):
# cd ../11_ops_cicd && bash deploy.sh
```

Step **10** (and **11**) needs your AgentCore Runtime ARN from lab 02.

---

## Diff any two steps

```bash
diff -ru 07_react_login 08_apprunner_health | less
```

---

## Architecture (step 10)

Diagrams (PNG + editable draw.io):  
[`10_agentcore_chat/architecture/`](./10_agentcore_chat/architecture/)

---

## Note vs the companion staged `-c stage=N` lab

Lab [`05.agentcore-production-deploy`](../05.agentcore-production-deploy/) ships the **same** product path (through stage 10, plus optional stage 11 ops) as **one** CDK codebase driven by stage flags instead of folders.  
See [`../05.agentcore-production-deploy/CLASSROOM_10_CDK_DEPLOYS.md`](../05.agentcore-production-deploy/CLASSROOM_10_CDK_DEPLOYS.md).

**These folders** are usually easier to study: each directory is the whole truth for that moment in the build. The classroom AWS account's live `LaukiSupportStack` tracks this progressive path (through `11_ops_cicd`), not lab 05.
