#!/usr/bin/env bash
# Fargate ops day — same as 12_fargate_alternative, plus ECS request-count
# autoscaling, a cost budget, and a GitHub Actions deploy role.
# Independent stack (default LaukiSupportFargateStack) — additive on top of
# whatever 12_fargate_alternative already deployed under that name.
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

# Only one GitHub OIDC provider per URL is allowed per AWS account. If
# 11_ops_cicd already created one, reuse it instead of letting CDK try
# (and fail) to create a duplicate.
if [ -z "${GITHUB_OIDC_PROVIDER_ARN:-}" ]; then
  EXISTING_OIDC="$(aws iam list-open-id-connect-providers \
    --query "OpenIDConnectProviderList[?contains(Arn,'token.actions.githubusercontent.com')].Arn | [0]" \
    --output text 2>/dev/null || true)"
  if [ -n "$EXISTING_OIDC" ] && [ "$EXISTING_OIDC" != "None" ]; then
    export GITHUB_OIDC_PROVIDER_ARN="$EXISTING_OIDC"
    echo "==> Reusing existing GitHub OIDC provider: $GITHUB_OIDC_PROVIDER_ARN"
  fi
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
echo "==> Fargate ops day  Stack=$STACK_NAME  Account=$CDK_DEFAULT_ACCOUNT Region=$AWS_REGION"
aws sts get-caller-identity
npx --yes cdk@2 bootstrap "aws://${CDK_DEFAULT_ACCOUNT}/${AWS_REGION}"

CTX=(-c "supportRuntimeArn=${SUPPORT_RUNTIME_ARN}" -c "stackName=${STACK_NAME}")
if [ -n "${BUDGET_ALERT_EMAIL:-}" ]; then
  CTX+=(-c "budgetAlertEmail=${BUDGET_ALERT_EMAIL}")
fi
if [ -n "${BUDGET_LIMIT_USD:-}" ]; then
  CTX+=(-c "budgetLimitUsd=${BUDGET_LIMIT_USD}")
fi
if [ -n "${GITHUB_REPO:-}" ]; then
  CTX+=(-c "githubRepo=${GITHUB_REPO}")
fi
if [ -n "${GITHUB_OIDC_PROVIDER_ARN:-}" ]; then
  CTX+=(-c "githubOidcProviderArn=${GITHUB_OIDC_PROVIDER_ARN}")
fi

npx --yes cdk@2 deploy "$STACK_NAME" --require-approval never "${CTX[@]}" "$@"
