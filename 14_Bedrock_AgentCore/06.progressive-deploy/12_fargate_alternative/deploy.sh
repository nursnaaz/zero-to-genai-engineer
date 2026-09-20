#!/usr/bin/env bash
# Fargate alternative — same app as step 10, ECS Fargate + ALB instead of App Runner.
# Independent stack (default name LaukiSupportFargateStack) — does not touch
# LaukiSupportStack (the App Runner demo).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/cdk"

export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
export STACK_NAME="${STACK_NAME:-LaukiSupportFargateStack}"

if [ -z "${SUPPORT_RUNTIME_ARN:-}" ]; then
  echo "ERROR: export SUPPORT_RUNTIME_ARN=arn:aws:bedrock-agentcore:..." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
echo "==> Fargate alternative  Stack=$STACK_NAME  Account=$CDK_DEFAULT_ACCOUNT Region=$AWS_REGION"
aws sts get-caller-identity
npx --yes cdk@2 bootstrap "aws://${CDK_DEFAULT_ACCOUNT}/${AWS_REGION}"

CTX=(-c "supportRuntimeArn=${SUPPORT_RUNTIME_ARN}" -c "stackName=${STACK_NAME}")
npx --yes cdk@2 deploy "$STACK_NAME" --require-approval never "${CTX[@]}" "$@"
