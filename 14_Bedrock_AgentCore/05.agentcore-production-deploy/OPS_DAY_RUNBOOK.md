# Ops Day runbook — CI/CD, scaling, cost, reliability

**Correct location:** the code for this is in
[`06.progressive-deploy/11_ops_cicd/`](../06.progressive-deploy/11_ops_cicd/),
*not* in this `05.agentcore-production-deploy/` folder. Verified via
`aws cloudformation describe-stacks --stack-name LaukiSupportStack` — the
live stack's `DeployStep` output only exists in the `06.progressive-deploy`
code shape, confirming that folder (specifically step 10) is what's actually
deployed. `05.agentcore-production-deploy` is a separate staged-CDK teaching
path (`-c stage=1..10`) that was never the one deployed to this account —
its own copy of stage 11/12 still exists there as a parallel, independent
enhancement, but it is not tied to anything live and isn't part of tonight's
demo.

This doc stays here only because it's the natural "ops" doc for the lab;
everything it references lives in `11_ops_cicd/`.

---

## ✅ Status as of tonight — already deployed and verified

- `bash deploy.sh` run from `11_ops_cicd/` under `AWS_PROFILE=inceptez`.
- **Real `cdk deploy` succeeded** (316s). Stack `LaukiSupportStack`,
  `UPDATE_COMPLETE`.
- **Full end-to-end smoke test passed**: real Cognito login (`demo` /
  `DemoUser1!`) → JWT → `/api/me` → `/api/chat` through CloudFront → got a
  real AgentCore response. Not a synth check — an actual HTTP round trip
  against the live app after the change.
- New resources confirmed live: `ApiAutoScaling` (min=1, max=3,
  concurrency=25 at first deploy — later bumped via CI demos; code now
  ships `concurrency=15`) attached to the App Runner service,
  `MonthlyCostBudget` ($10/mo that night, 80% alert → `nursnaaz@gmail.com`;
  folder default is `$15` if you omit `BUDGET_LIMIT_USD`),
  `GithubActionsDeployRole`.
- **One real side effect worth knowing before class**: attaching an auto
  scaling config to an existing App Runner service is a
  *replacement-triggering* property in CloudFormation — it silently
  recreated the App Runner service (new internal URL) rather than updating
  it in place. **The public CloudFront URL did not change** and the app
  stayed reachable — CloudFront's origin config was updated to the new
  service in the same deploy — but this is exactly the kind of "surprise
  diff" worth calling out live tomorrow: *"a one-line CDK change can mean
  more than it looks like — that's why you read the diff before merging."*
  If you ever see App Runner's URL change after a `cdk deploy` you didn't
  expect to be disruptive, this is why.

Current live values:

```
CloudFrontUrl   = https://d3n10wl4lfhw96.cloudfront.net
AppRunnerUrl    = https://zjkac72pya.us-east-1.awsapprunner.com
UserPoolId      = us-east-1_fr1k1oMUN
ClientId        = 27cp4cqpoum8dbp9g8pfqodo5l
Demo login      = demo / DemoUser1!
GithubActionsDeployRoleArn =
  arn:aws:iam::899736802567:role/LaukiSupportStack-GithubActionsDeployRole3AEBE7B4-tZ9vkcXKC5Iw
```

Still to confirm live (in progress): GitHub secrets set, a real dry-run PR
through the `plan`/`deploy` Actions jobs. This doc is updated again once
that's done.

---

## Tomorrow — live demo script (~30 min)

### Part 1 — CI/CD (10 min): "nobody deploys from a laptop"

1. Recap the running app (login `demo` / `DemoUser1!`, send a message).
2. On a fresh branch, change one visible line in
   `06.progressive-deploy/11_ops_cicd/cdk/stack.py` — e.g. the
   `max_concurrency=15` in the `ApiAutoScaling` block (bump it to `20`).
   Push, open a PR against `main`.
3. Actions tab: the `plan` job runs, posts a `cdk diff` comment on the PR.
   Read the diff out loud.
4. Merge the PR. Actions tab: `deploy` job runs `cdk deploy` for real.
5. Confirm in the App Runner console / via
   `aws apprunner list-auto-scaling-configurations` that the new value
   landed.

**Line to land:** *"Nobody ran `cdk deploy` from anyone's laptop. A
teammate — or you — reviewed the diff before AWS ever saw it."*

### Part 2 — Scaling (8 min): watch it happen

Best version: the whole class hits the CloudFront URL and sends a chat
message within the same 30 seconds. Have the **App Runner console →
Metrics** tab open on "Active instances" beforehand.

Backup:

```bash
CF=https://d3n10wl4lfhw96.cloudfront.net
for i in $(seq 1 60); do curl -s -o /dev/null "$CF/health" & done; wait
```

**Line to land:** *"We capped max at 3 tonight on purpose — the cap is a
cost decision, not a technical limit."*

### Part 3 — Cost (7 min)

1. AWS Budgets console → the $10/mo budget, 80% email alert to
   `nursnaaz@gmail.com`.
2. CloudWatch GenAI Observability dashboard → pull token usage for a
   session → cost-per-conversation math live. This is the "cost-per-task"
   number that actually gets tracked in production, not the total AWS bill.

### Part 4 — Reliability (10 min, scratch branch only)

1. Show `health_check_configuration` in `stack.py` — App Runner
   health-checks `/health` every 15s; if a *new deployment's* instances
   fail health checks, App Runner **automatically rolls back**.
2. On a scratch branch, make `/health` in `api/main.py` return a 500
   temporarily. Push → merge → CI deploys it.
3. Watch the App Runner console: the new deployment fails health checks and
   rolls back on its own within ~1–2 minutes.
4. Revert immediately after — don't leave the broken commit on `main`.

**Line to land:** *"Nobody paged anyone. The platform caught its own bad
deploy."*

---

## Cleanup after class

- `max_size=3` already caps the scaling blast radius.
- The $10 budget alert stays — harmless, just email.
- `GithubActionsDeployRole` has `AdministratorAccess` for tonight's speed —
  tighten to a scoped CDK-deploy policy before reusing this pattern beyond
  a classroom demo.
- Full teardown: see lab 05 README §9 Cleanup (same underlying AWS
  resources either way).
