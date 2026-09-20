#!/usr/bin/env python3
from __future__ import annotations

import os
import aws_cdk as cdk
from stack import LaukiSupportFargateStack

app = cdk.App()
stack_name = (
    app.node.try_get_context("stackName")
    or os.environ.get("STACK_NAME")
    or "LaukiSupportFargateStack"
)
runtime_arn = (
    app.node.try_get_context("supportRuntimeArn")
    or os.environ.get("SUPPORT_RUNTIME_ARN")
    or ""
).strip()
if not runtime_arn:
    raise SystemExit(
        "Need SUPPORT_RUNTIME_ARN\n"
        "  export SUPPORT_RUNTIME_ARN=arn:aws:bedrock-agentcore:..."
    )
budget_alert_email = (
    app.node.try_get_context("budgetAlertEmail")
    or os.environ.get("BUDGET_ALERT_EMAIL")
    or ""
).strip()
budget_limit_usd = float(
    app.node.try_get_context("budgetLimitUsd")
    or os.environ.get("BUDGET_LIMIT_USD")
    or "15"
)
github_repo = (
    app.node.try_get_context("githubRepo")
    or os.environ.get("GITHUB_REPO")
    or "nursnaaz/zero-to-genai-engineer"
).strip()
github_oidc_provider_arn = (
    app.node.try_get_context("githubOidcProviderArn")
    or os.environ.get("GITHUB_OIDC_PROVIDER_ARN")
    or ""
).strip()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION")
    or os.environ.get("AWS_REGION")
    or "us-east-1",
)

LaukiSupportFargateStack(
    app,
    stack_name,
    support_runtime_arn=runtime_arn,
    budget_alert_email=budget_alert_email,
    budget_limit_usd=budget_limit_usd,
    github_repo=github_repo,
    github_oidc_provider_arn=github_oidc_provider_arn,
    env=env,
    description="Lauki Support — Fargate + ALB (step 12) + autoscaling/budget/CI (step 13)",
)
app.synth()
