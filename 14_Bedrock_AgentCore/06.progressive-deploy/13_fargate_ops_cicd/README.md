# Step 13 — Fargate ops day (autoscaling + cost budget + GitHub Actions)

Folder: `13_fargate_ops_cicd`

The Fargate equivalent of [`11_ops_cicd`](../11_ops_cicd/) — same idea
(scaling guardrail, cost budget, CI-deployed via OIDC), applied to the
[`12_fargate_alternative`](../12_fargate_alternative/) stack instead of the
App Runner one. Same stack name (`LaukiSupportFargateStack`) as step 12 —
this is additive on top of what's already deployed there, not a new stack.

## What's different from the App Runner version

| | App Runner (11_ops_cicd) | Fargate (this folder) |
|---|---|---|
| Scaling mechanism | `apprunner.CfnAutoScalingConfiguration` (min/max/`max_concurrency`) | Application Auto Scaling on the ECS service (`auto_scale_task_count` + `scale_on_request_count`) — same idea, ALB-request-count-driven instead of App Runner's built-in concurrency metric |
| Cost budget | `budgets.CfnBudget`, EMAIL subscriber | Identical — copied as-is, compute-type-agnostic |
| GitHub OIDC provider | Created fresh | **Reused** — AWS allows only one OIDC provider per URL per account, and `11_ops_cicd` already made one. `deploy.sh` auto-detects it via `aws iam list-open-id-connect-providers` so this never tries to create a duplicate. |
| GitHub Actions deploy role | Its own role, scoped to `LaukiSupportStack` | Its own separate role, scoped to `LaukiSupportFargateStack` |

## Deploy

```bash
cd 06.progressive-deploy/13_fargate_ops_cicd
export SUPPORT_RUNTIME_ARN='arn:aws:bedrock-agentcore:...'
export BUDGET_ALERT_EMAIL='you@example.com'   # optional
export BUDGET_LIMIT_USD=10                     # optional, default 15
bash deploy.sh
```

## Verify

```bash
aws cloudformation describe-stacks --stack-name LaukiSupportFargateStack --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='AutoScalingLimits' || OutputKey=='BudgetAlert' || OutputKey=='GithubActionsDeployRoleArn']"
```

App itself still logs in and chats exactly like step 12 — this folder only
adds operations, not features.

## CI/CD

[`.github/workflows/agentcore-fargate-cdk-deploy.yml`](../../../../.github/workflows/agentcore-fargate-cdk-deploy.yml)
at the repo root — `cdk diff` on PRs touching this folder, `cdk deploy` on
merge to `main`. Needs its own repo secret (`AWS_FARGATE_DEPLOY_ROLE_ARN`,
from this stack's `GithubActionsDeployRoleArn` output) — separate from the
App Runner pipeline's `AWS_DEPLOY_ROLE_ARN` secret, since they're different
roles for different stacks. Reuses the same `SUPPORT_RUNTIME_ARN` secret
and `BUDGET_ALERT_EMAIL` / `BUDGET_LIMIT_USD` variables.

## What changed vs step 12

ADD Application Auto Scaling on the ECS service (min=1, max=3,
requests-per-target=10) via `scale_on_request_count`. ADD an optional
monthly `budgets.CfnBudget` with an 80%-threshold email alert. ADD a
GitHub Actions OIDC deploy role (imports the existing OIDC provider from
`11_ops_cicd` rather than creating a duplicate).
