# Step 11 — Ops day: auto scaling + cost budget + GitHub Actions deploy role

Folder: `11_ops_cicd`

Same app as step 10 — this folder only adds operations, not features.

## Deploy

```bash
cd 06.progressive-deploy/11_ops_cicd
export SUPPORT_RUNTIME_ARN='arn:aws:bedrock-agentcore:...'
export BUDGET_ALERT_EMAIL='you@example.com'   # optional — omit to skip the budget
export BUDGET_LIMIT_USD=15                     # optional, default 15
bash deploy.sh
```

## Verify

```bash
aws cloudformation describe-stacks --stack-name LaukiSupportStack --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='AutoScalingLimits' || OutputKey=='BudgetAlert' || OutputKey=='GithubActionsDeployRoleArn']"
aws apprunner list-auto-scaling-configurations --region us-east-1 \
  --query "AutoScalingConfigurationSummaryList[].AutoScalingConfigurationName"
```

Expect `AutoScalingLimits` ≈ `min=1 max=3 concurrency=15`. `BudgetAlert` only appears if you set `BUDGET_ALERT_EMAIL`.

The app itself still logs in and chats exactly like step 10 — nothing about
the user-facing product changed.

## See the delta vs previous folder

```bash
diff -ru ../10_agentcore_chat . | less
```

## What changed vs previous

ADD `apprunner.CfnAutoScalingConfiguration` (min=1, max=3, concurrency=15)
wired onto the existing App Runner service. ADD an optional monthly
`budgets.CfnBudget` with an 80%-threshold email alert (skipped if
`BUDGET_ALERT_EMAIL` is unset; limit defaults to `$15` / mo via
`BUDGET_LIMIT_USD`). ADD a GitHub Actions OIDC provider + IAM role
(`GithubActionsDeployRoleArn` output) so CI can `cdk deploy` this stack
without long-lived AWS keys — see
[`../../05.agentcore-production-deploy/OPS_DAY_RUNBOOK.md`](../../05.agentcore-production-deploy/OPS_DAY_RUNBOOK.md)
for the full setup + live demo script, and
[`.github/workflows/agentcore-cdk-deploy.yml`](../../../.github/workflows/agentcore-cdk-deploy.yml)
at the repo root for the pipeline itself.

**Done — full stack, now with scaling limits, a cost guardrail, and a CI
path to deploy it.**

Same CloudFormation stack name: **`LaukiSupportStack`**
(so step 11 updates what step 10 deployed — this is the folder that matches
what's actually live in the classroom AWS account, not
`05.agentcore-production-deploy`, which is a separate staged-CDK teaching
path that was never the one deployed here).
