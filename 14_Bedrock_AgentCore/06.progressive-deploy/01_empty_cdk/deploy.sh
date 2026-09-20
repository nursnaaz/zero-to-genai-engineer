#!/usr/bin/env bash
# Classroom step 01 — deploy this folder's stack
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/cdk"

export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
export STACK_NAME="${STACK_NAME:-LaukiSupportStack}"

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
echo "==> Step 01  Stack=$STACK_NAME  Account=$CDK_DEFAULT_ACCOUNT Region=$AWS_REGION"
aws sts get-caller-identity
npx --yes cdk@2 bootstrap "aws://${CDK_DEFAULT_ACCOUNT}/${AWS_REGION}"
CTX=(-c "stackName=${STACK_NAME}")
npx --yes cdk@2 deploy "$STACK_NAME" --require-approval never "${CTX[@]}" "$@"
