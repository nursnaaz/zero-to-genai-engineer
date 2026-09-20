#!/usr/bin/env bash
# Classroom: deploy stages 1→12
#   bash cdk/deploy.sh 1
#   bash cdk/deploy.sh 2
#   ...
#   SUPPORT_RUNTIME_ARN=arn:... bash cdk/deploy.sh 10
#   SUPPORT_RUNTIME_ARN=arn:... BUDGET_ALERT_EMAIL=you@example.com bash cdk/deploy.sh 11
#   SUPPORT_RUNTIME_ARN=arn:... bash cdk/deploy.sh 12

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"

STAGE="${1:-${CDK_STAGE:-10}}"
if [[ ! "$STAGE" =~ ^[0-9]+$ ]]; then
  echo "Usage: bash cdk/deploy.sh <1-12>" >&2
  exit 1
fi
shift || true

# NOTE: was `-eq 10` — that silently dropped SUPPORT_RUNTIME_ARN for stages
# 11/12 (both still require it, app.py checks `stage >= 10`).
if [ "$STAGE" -ge 10 ] && [ -z "${SUPPORT_RUNTIME_ARN:-}" ]; then
  echo "ERROR: stage $STAGE needs SUPPORT_RUNTIME_ARN (required from stage 10 up)" >&2
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

echo "==> Account=$CDK_DEFAULT_ACCOUNT Region=$AWS_REGION Stage=$STAGE"
aws sts get-caller-identity

npx --yes cdk@2 bootstrap "aws://${CDK_DEFAULT_ACCOUNT}/${AWS_REGION}"

CTX=(-c "stage=${STAGE}")
if [ -n "${SUPPORT_RUNTIME_ARN:-}" ]; then
  CTX+=(-c "supportRuntimeArn=${SUPPORT_RUNTIME_ARN}")
fi
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

echo "==> cdk deploy ${CTX[*]} $*"
npx --yes cdk@2 deploy --require-approval never "${CTX[@]}" "$@"
