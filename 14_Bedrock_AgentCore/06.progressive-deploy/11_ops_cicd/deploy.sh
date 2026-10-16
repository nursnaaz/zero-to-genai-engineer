#!/usr/bin/env bash
# Classroom step 11 — ops day: auto scaling + cost budget + GitHub Actions deploy role
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/cdk"

export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
export STACK_NAME="${STACK_NAME:-LaukiSupportStack}"

if [ -z "${SUPPORT_RUNTIME_ARN:-}" ]; then
  echo "ERROR: export SUPPORT_RUNTIME_ARN=arn:aws:bedrock-agentcore:..." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  if [ $OS = "Windows_NT" ]; then
    python -m venv .venv
  else
    python3 -m venv .venv
  fi
fi

if [ -f .venv/Scripts/activate ]; then
  # shellcheck disable=SC1091
  source .venv/Scripts/activate
elif [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

pip install -q -r requirements.txt

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
echo "==> Step 11  Stack=$STACK_NAME  Account=$CDK_DEFAULT_ACCOUNT Region=$AWS_REGION"
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
