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
    env=env,
    description="Lauki Support — Fargate + ALB alternative to App Runner (step 10 app, different compute)",
)
app.synth()
