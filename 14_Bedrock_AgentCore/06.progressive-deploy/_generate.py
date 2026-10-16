#!/usr/bin/env python3
"""
Generate 06.progressive-deploy/01..10 — cumulative, self-contained folders.

Run from 14_Bedrock_AgentCore/ or this directory:
  python3 06.progressive-deploy/_generate.py

Each folder can `bash deploy.sh` independently.
Same stack name (default LaukiSupportStack) so deploy 01→02→… updates one CFN stack.
Override with: export STACK_NAME=LaukiSupportClassA

Open folder N and N+1 side-by-side to teach the delta.

Note: the React source these folders copy into steps 07-10 lives in the
companion lab 05.agentcore-production-deploy/web/, not inside this folder.
"""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LAB = ROOT.parent / "05.agentcore-production-deploy"
WEB_SRC = LAB / "web"

STEPS = [
    ("01_empty_cdk", "Empty CDK stack (SSM marker)"),
    ("02_cognito_pool", "Cognito User Pool"),
    ("03_cognito_client", "Cognito SPA app client"),
    ("04_demo_user", "Demo user demo / DemoUser1!"),
    ("05_s3_ui_bucket", "Private S3 bucket for UI"),
    ("06_cloudfront", "CloudFront + placeholder HTML"),
    ("07_react_login", "React Cognito login (chat locked)"),
    ("08_apprunner_health", "App Runner FastAPI /health"),
    ("09_jwt_lock", "JWT lock on /api/me"),
    ("10_agentcore_chat", "AgentCore /api/chat — full demo"),
]

CDK_JSON = """{
  "app": "python app.py",
  "watch": {
    "include": ["**"],
    "exclude": [
      "README.md",
      "cdk*.json",
      "requirements*.txt",
      "**/__pycache__",
      "**/.venv",
      "**/node_modules"
    ]
  },
  "context": {
    "@aws-cdk/aws-s3:createDefaultLoggingPolicy": true,
    "@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy": true
  }
}
"""

REQUIREMENTS = "aws-cdk-lib>=2.170.0,<3\nconstructs>=10.0.0,<11\n"

DEMO_USER = "demo"
DEMO_PASSWORD = "DemoUser1!"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n") if content.startswith("\n") else content)
    if not content.endswith("\n"):
        path.write_text(path.read_text() + "\n")


def deploy_sh(step_num: int, needs_runtime: bool) -> str:
    runtime_block = ""
    if needs_runtime:
        runtime_block = """
if [ -z "${SUPPORT_RUNTIME_ARN:-}" ]; then
  echo "ERROR: export SUPPORT_RUNTIME_ARN=arn:aws:bedrock-agentcore:..." >&2
  exit 1
fi
"""
    ctx = (
        'CTX=(-c "supportRuntimeArn=${SUPPORT_RUNTIME_ARN}" -c "stackName=${STACK_NAME}")'
        if needs_runtime
        else 'CTX=(-c "stackName=${STACK_NAME}")'
    )
    return f"""#!/usr/bin/env bash
# Classroom step {step_num:02d} — deploy this folder's stack
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/cdk"

export AWS_REGION="${{AWS_REGION:-us-east-1}}"
export AWS_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_REGION="$AWS_REGION"
export CDK_DEFAULT_ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
export STACK_NAME="${{STACK_NAME:-LaukiSupportStack}}"
{runtime_block}
if [ ! -d .venv ]; then
  if [[ "${{OS:-}}" == "Windows_NT" || "${{OSTYPE:-}}" == msys* || "${{OSTYPE:-}}" == cygwin* || "$(uname -s 2>/dev/null)" == MINGW* || "$(uname -s 2>/dev/null)" == MSYS* || "$(uname -s 2>/dev/null)" == CYGWIN* ]]; then
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
echo "==> Step {step_num:02d}  Stack=$STACK_NAME  Account=$CDK_DEFAULT_ACCOUNT Region=$AWS_REGION"
aws sts get-caller-identity
npx --yes cdk@2 bootstrap "aws://${{CDK_DEFAULT_ACCOUNT}}/${{AWS_REGION}}"
{ctx}
npx --yes cdk@2 deploy "$STACK_NAME" --require-approval never "${{CTX[@]}}" "$@"
"""


def app_py(needs_runtime: bool) -> str:
    if needs_runtime:
        return '''\
#!/usr/bin/env python3
from __future__ import annotations

import os
import aws_cdk as cdk
from stack import LaukiSupportStack

app = cdk.App()
stack_name = (
    app.node.try_get_context("stackName")
    or os.environ.get("STACK_NAME")
    or "LaukiSupportStack"
)
runtime_arn = (
    app.node.try_get_context("supportRuntimeArn")
    or os.environ.get("SUPPORT_RUNTIME_ARN")
    or ""
).strip()
if not runtime_arn:
    raise SystemExit(
        "Need SUPPORT_RUNTIME_ARN\\n"
        "  export SUPPORT_RUNTIME_ARN=arn:aws:bedrock-agentcore:..."
    )

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION")
    or os.environ.get("AWS_REGION")
    or "us-east-1",
)

LaukiSupportStack(
    app,
    stack_name,
    support_runtime_arn=runtime_arn,
    env=env,
    description="Lauki Support classroom step 10",
)
app.synth()
'''
    return '''\
#!/usr/bin/env python3
from __future__ import annotations

import os
import aws_cdk as cdk
from stack import LaukiSupportStack

app = cdk.App()
stack_name = (
    app.node.try_get_context("stackName")
    or os.environ.get("STACK_NAME")
    or "LaukiSupportStack"
)
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION")
    or os.environ.get("AWS_REGION")
    or "us-east-1",
)

LaukiSupportStack(
    app,
    stack_name,
    env=env,
)
app.synth()
'''


def stack_imports(step: int) -> str:
    lines = [
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "import aws_cdk as cdk",
        "from aws_cdk import CfnOutput, RemovalPolicy, Stack",
        "from aws_cdk import aws_ssm as ssm",
        "from constructs import Construct",
    ]
    if step >= 2:
        lines.insert(-1, "from aws_cdk import aws_cognito as cognito")
    if step >= 4:
        lines.insert(-1, "from aws_cdk import custom_resources as cr")
    if step >= 5:
        lines.insert(-1, "from aws_cdk import aws_s3 as s3")
    if step >= 6:
        lines.insert(-1, "from aws_cdk import Duration")
        lines.insert(-1, "from aws_cdk import aws_cloudfront as cloudfront")
        lines.insert(-1, "from aws_cdk import aws_cloudfront_origins as origins")
        lines.insert(-1, "from aws_cdk import aws_s3_deployment as s3deploy")
    if step >= 8:
        lines.insert(-1, "from pathlib import Path")
        lines.insert(-1, "from aws_cdk import aws_apprunner as apprunner")
        lines.insert(-1, "from aws_cdk import aws_ecr_assets as ecr_assets")
        lines.insert(-1, "from aws_cdk import aws_iam as iam")
    return "\n".join(lines) + "\n"


def build_stack(step: int) -> str:
    """Plain cumulative stack — no stage flags. Construct IDs stable across folders."""
    parts: list[str] = [stack_imports(step)]

    if step >= 8:
        parts.append(
            'ROOT = Path(__file__).resolve().parent.parent\n'
            'API_DIR = ROOT / "api"\n'
            'WEB_DIR = ROOT / "web"\n'
        )
    elif step >= 7:
        parts.append(
            'from pathlib import Path\n'
            'ROOT = Path(__file__).resolve().parent.parent\n'
            'WEB_DIR = ROOT / "web"\n'
        )

    if step >= 4:
        parts.append(f'DEMO_USERNAME = "{DEMO_USER}"\nDEMO_PASSWORD = "{DEMO_PASSWORD}"\n')

    # class header
    if step >= 10:
        init_sig = (
            "    def __init__(\n"
            "        self,\n"
            "        scope: Construct,\n"
            "        construct_id: str,\n"
            "        *,\n"
            "        support_runtime_arn: str,\n"
            "        **kwargs: Any,\n"
            "    ) -> None:\n"
            "        super().__init__(scope, construct_id, **kwargs)\n"
            "        region = Stack.of(self).region\n"
        )
    else:
        init_sig = (
            "    def __init__(\n"
            "        self,\n"
            "        scope: Construct,\n"
            "        construct_id: str,\n"
            "        **kwargs: Any,\n"
            "    ) -> None:\n"
            "        super().__init__(scope, construct_id, **kwargs)\n"
        )
        if step >= 2:
            init_sig += "        region = Stack.of(self).region\n"

    parts.append(
        f'class LaukiSupportStack(Stack):\n'
        f'{init_sig}\n'
        f'        # Unique per STACK_NAME so parallel classroom stacks do not collide\n'
        f'        _safe = "".join(\n'
        f'            ch.lower() if ch.isalnum() else "-" for ch in construct_id\n'
        f'        ).strip("-")[:24]\n'
        f'        CfnOutput(self, "DeployStep", value="{step}")\n'
        f'        CfnOutput(\n'
        f'            self,\n'
        f'            "StepHint",\n'
        f'            value="{STEPS[step - 1][1]}",\n'
        f'        )\n'
        f'        CfnOutput(self, "StackName", value=construct_id)\n\n'
        f'        ssm.StringParameter(\n'
        f'            self,\n'
        f'            "StageMarker",\n'
        f'            parameter_name=f"/lauki-support/{{_safe}}/deploy-stage",\n'
        f'            string_value="{step}",\n'
        f'            description="Classroom step folder",\n'
        f'        )\n'
    )

    if step >= 2:
        parts.append(
            """
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"lauki-users-{_safe}",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
"""
        )

    if step >= 3:
        parts.append(
            """
        user_pool_client = user_pool.add_client(
            "SpaClient",
            user_pool_client_name="lauki-support-spa",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            generate_secret=False,
            prevent_user_existence_errors=True,
        )
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
"""
        )

    if step >= 4:
        parts.append(
            """
        create_user = cr.AwsCustomResource(
            self,
            "CreateDemoUser",
            on_create=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminCreateUser",
                parameters={
                    "UserPoolId": user_pool.user_pool_id,
                    "Username": DEMO_USERNAME,
                    "TemporaryPassword": DEMO_PASSWORD,
                    "MessageAction": "SUPPRESS",
                    "UserAttributes": [
                        {"Name": "email", "Value": "demo@example.com"},
                        {"Name": "email_verified", "Value": "true"},
                    ],
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"demo-user-{DEMO_USERNAME}"
                ),
                ignore_error_codes_matching="UsernameExistsException",
            ),
            on_update=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminCreateUser",
                parameters={
                    "UserPoolId": user_pool.user_pool_id,
                    "Username": DEMO_USERNAME,
                    "TemporaryPassword": DEMO_PASSWORD,
                    "MessageAction": "SUPPRESS",
                    "UserAttributes": [
                        {"Name": "email", "Value": "demo@example.com"},
                        {"Name": "email_verified", "Value": "true"},
                    ],
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"demo-user-{DEMO_USERNAME}"
                ),
                ignore_error_codes_matching="UsernameExistsException",
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )
        set_password = cr.AwsCustomResource(
            self,
            "SetDemoPassword",
            on_create=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminSetUserPassword",
                parameters={
                    "UserPoolId": user_pool.user_pool_id,
                    "Username": DEMO_USERNAME,
                    "Password": DEMO_PASSWORD,
                    "Permanent": True,
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"demo-password-{DEMO_USERNAME}"
                ),
            ),
            on_update=cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminSetUserPassword",
                parameters={
                    "UserPoolId": user_pool.user_pool_id,
                    "Username": DEMO_USERNAME,
                    "Password": DEMO_PASSWORD,
                    "Permanent": True,
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"demo-password-{DEMO_USERNAME}"
                ),
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )
        set_password.node.add_dependency(create_user)
        CfnOutput(self, "DemoUsername", value=DEMO_USERNAME)
        CfnOutput(self, "DemoPassword", value=DEMO_PASSWORD)
"""
        )

    if step >= 5:
        parts.append(
            """
        ui_bucket = s3.Bucket(
            self,
            "UiBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        CfnOutput(self, "UiBucketName", value=ui_bucket.bucket_name)
"""
        )

    # API before CF when step >= 8 (same as parent staged stack)
    if step >= 8:
        auth_env = ""
        if step >= 9:
            auth_env = """
        env_vars.extend(
            [
                apprunner.CfnService.KeyValuePairProperty(
                    name="COGNITO_REGION", value=region
                ),
                apprunner.CfnService.KeyValuePairProperty(
                    name="COGNITO_USER_POOL_ID",
                    value=user_pool.user_pool_id,
                ),
                apprunner.CfnService.KeyValuePairProperty(
                    name="COGNITO_CLIENT_ID",
                    value=user_pool_client.user_pool_client_id,
                ),
                apprunner.CfnService.KeyValuePairProperty(
                    name="AUTH_DISABLED", value="false"
                ),
            ]
        )
"""
        else:
            auth_env = """
        env_vars.append(
            apprunner.CfnService.KeyValuePairProperty(
                name="AUTH_DISABLED", value="true"
            )
        )
"""

        runtime_block = ""
        if step >= 10:
            runtime_block = """
        endpoint_arn = f"{support_runtime_arn}/runtime-endpoint/DEFAULT"
        instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agentcore:InvokeAgentRuntime",
                    "bedrock-agentcore:InvokeAgentRuntimeForUser",
                ],
                resources=[support_runtime_arn, endpoint_arn],
            )
        )
        env_vars.append(
            apprunner.CfnService.KeyValuePairProperty(
                name="SUPPORT_RUNTIME_ARN",
                value=support_runtime_arn,
            )
        )
        CfnOutput(self, "SupportRuntimeArn", value=support_runtime_arn)
"""

        parts.append(
            f"""
        api_image = ecr_assets.DockerImageAsset(
            self,
            "ApiImage",
            directory=str(API_DIR),
            platform=ecr_assets.Platform.LINUX_AMD64,
            asset_name="lauki-support-api",
        )
        ecr_access_role = iam.Role(
            self,
            "AppRunnerEcrAccessRole",
            assumed_by=iam.ServicePrincipal("build.apprunner.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSAppRunnerServicePolicyForECRAccess"
                )
            ],
        )
        api_image.repository.grant_pull(ecr_access_role)

        instance_role = iam.Role(
            self,
            "AppRunnerInstanceRole",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com"),
        )

        env_vars = [
            apprunner.CfnService.KeyValuePairProperty(
                name="AWS_REGION", value=region
            ),
            apprunner.CfnService.KeyValuePairProperty(
                name="CORS_ORIGINS", value="*"
            ),
        ]
{auth_env}
{runtime_block}
        api_service = apprunner.CfnService(
            self,
            "ApiService",
            service_name=f"lauki-api-{{_safe}}"[:40],
            source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                authentication_configuration=apprunner.CfnService.AuthenticationConfigurationProperty(
                    access_role_arn=ecr_access_role.role_arn,
                ),
                auto_deployments_enabled=False,
                image_repository=apprunner.CfnService.ImageRepositoryProperty(
                    image_identifier=api_image.image_uri,
                    image_repository_type="ECR",
                    image_configuration=apprunner.CfnService.ImageConfigurationProperty(
                        port="8000",
                        runtime_environment_variables=env_vars,
                    ),
                ),
            ),
            instance_configuration=apprunner.CfnService.InstanceConfigurationProperty(
                cpu="1024",
                memory="2048",
                instance_role_arn=instance_role.role_arn,
            ),
            health_check_configuration=apprunner.CfnService.HealthCheckConfigurationProperty(
                protocol="HTTP",
                path="/health",
                interval=15,
                timeout=5,
                healthy_threshold=1,
                unhealthy_threshold=5,
            ),
        )
        api_service.node.add_dependency(ecr_access_role)
        api_service.node.add_dependency(instance_role)
        CfnOutput(
            self,
            "AppRunnerUrl",
            value=f"https://{{api_service.attr_service_url}}",
        )
"""
        )

    if step >= 6:
        api_behaviors = ""
        if step >= 8:
            api_behaviors = """
        api_origin = origins.HttpOrigin(
            api_service.attr_service_url,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
        )
        api_behavior = cloudfront.BehaviorOptions(
            origin=api_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
            cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        )
        additional["/api/*"] = api_behavior
        additional["/health"] = api_behavior
"""
        parts.append(
            f"""
        oac = cloudfront.S3OriginAccessControl(
            self,
            "UiOac",
            signing=cloudfront.Signing.SIGV4_ALWAYS,
        )
        s3_origin = origins.S3BucketOrigin.with_origin_access_control(
            ui_bucket,
            origin_access_control=oac,
        )
        additional: dict[str, cloudfront.BehaviorOptions] = {{}}
{api_behaviors}
        distribution = cloudfront.Distribution(
            self,
            "UiDistribution",
            comment="lauki-support-ui-cdk",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                compress=True,
            ),
            additional_behaviors=additional or None,
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
            ],
        )
        CfnOutput(
            self,
            "CloudFrontUrl",
            value=f"https://{{distribution.distribution_domain_name}}",
        )
"""
        )

    if step == 6:
        parts.append(
            """
        placeholder = s3deploy.Source.data(
            "index.html",
            \"\"\"<!doctype html><html><head><meta charset="utf-8"/>
<title>Lauki — Step 06</title></head>
<body style="font-family:sans-serif;background:#0b1220;color:#e8eefc;padding:2rem">
<h1>Classroom Step 06</h1>
<p>CloudFront + S3 are live. Next folder adds the React Cognito login UI.</p>
</body></html>\"\"\",
        )
        s3deploy.BucketDeployment(
            self,
            "DeployPlaceholder",
            sources=[placeholder],
            destination_bucket=ui_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )
"""
        )

    if step >= 7:
        chat = "True" if step >= 10 else "False"
        # Need Duration import for step 7 - already from step 6
        # Need s3deploy - already from step 6
        # For step 7, stack_imports may not include Duration if we only add at 6 - step 7 includes 6 so OK
        # But step 7 needs pathlib WEB_DIR - added
        # step 7 needs s3deploy and cloudfront - from step 6 block which is included... wait step 7 includes step >= 6 so Duration and s3deploy are imported. Good.

        # Fix: step 7 imports - stack_imports(7) needs pathlib, Duration, cloudfront, s3deploy
        # Currently stack_imports only adds pathlib for step>=8 or separately for >=7. Good.
        # Duration/cloudfront/s3deploy only if step >= 6. Good.

        parts.append(
            f"""
        chat_enabled = {chat}
        config = {{
            "step": {step},
            "stage": {step},
            "authRequired": True,
            "chatEnabled": chat_enabled,
            "region": region,
            "apiBase": "",
            "userPoolId": user_pool.user_pool_id,
            "clientId": user_pool_client.user_pool_client_id,
        }}
        web_asset = s3deploy.Source.asset(
            str(WEB_DIR),
            exclude=["node_modules", "dist", ".git"],
            bundling=cdk.BundlingOptions(
                image=cdk.DockerImage.from_registry(
                    "public.ecr.aws/docker/library/node:20-alpine"
                ),
                user="root",
                environment={{"VITE_API_BASE": ""}},
                command=[
                    "sh",
                    "-c",
                    "npm ci && npm run build && cp -r dist/. /asset-output/",
                ],
            ),
        )
        cognito_config = s3deploy.Source.json_data("config.json", config)
        s3deploy.BucketDeployment(
            self,
            "DeployUi",
            sources=[web_asset, cognito_config],
            destination_bucket=ui_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
            memory_limit=1024,
        )
"""
        )

    return "\n".join(parts)


def api_main(step: int) -> str:
    """Progressive API source."""
    if step == 8:
        return '''\
"""Step 08 — health only. Auth + chat arrive in later folders."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Lauki Support API", version="0.8.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "auth": "disabled", "step": 8}
'''
    if step == 9:
        return '''\
"""Step 09 — Cognito JWT lock on /api/me. Chat arrives in step 10."""
from __future__ import annotations

import os
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

app = FastAPI(title="Lauki Support API", version="0.9.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bearer = HTTPBearer(auto_error=False)
_jwks_client: PyJWKClient | None = None


def _auth_disabled() -> bool:
    return os.getenv("AUTH_DISABLED", "").lower() in {"1", "true", "yes"}


def _cognito_configured() -> bool:
    return bool(
        (os.getenv("COGNITO_USER_POOL_ID") or "").strip()
        and (os.getenv("COGNITO_CLIENT_ID") or "").strip()
    )


def _region() -> str:
    return os.getenv("COGNITO_REGION") or os.getenv("AWS_REGION") or "us-east-1"


def _issuer() -> str:
    pool = os.environ["COGNITO_USER_POOL_ID"].strip()
    return f"https://cognito-idp.{_region()}.amazonaws.com/{pool}"


def _jwks() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{_issuer()}/.well-known/jwks.json")
    return _jwks_client


def require_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    if _auth_disabled() or not _cognito_configured():
        return {"sub": "local-dev", "cognito:username": "local-dev"}
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Login required")
    token = creds.credentials
    client_id = os.environ["COGNITO_CLIENT_ID"].strip()
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=_issuer(),
            options={"require": ["exp", "iss", "sub"], "verify_aud": False},
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc
    if claims.get("token_use") == "id" and claims.get("aud") != client_id:
        raise HTTPException(status_code=401, detail="Token audience mismatch")
    return claims


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "auth": "disabled" if _auth_disabled() or not _cognito_configured() else "cognito",
        "step": 9,
    }


@app.get("/api/me")
def me(user: dict[str, Any] = Depends(require_user)) -> dict[str, Any]:
    return {
        "sub": user.get("sub"),
        "username": user.get("cognito:username") or user.get("username") or user.get("sub"),
    }
'''
    # step 10 — copy lab api
    return (LAB / "api" / "main.py").read_text()


def api_requirements(step: int) -> str:
    if step == 8:
        return "fastapi>=0.110.0\nuvicorn[standard]>=0.27.0\n"
    if step == 9:
        return (
            "fastapi>=0.110.0\n"
            "uvicorn[standard]>=0.27.0\n"
            "PyJWT[crypto]>=2.8.0\n"
        )
    return (LAB / "api" / "requirements.txt").read_text()


def copy_web(dest: Path) -> None:
    """Copy React sources from lab (exclude node_modules/dist)."""
    dest.mkdir(parents=True, exist_ok=True)
    for name in [
        "package.json",
        "package-lock.json",
        "vite.config.js",
        "index.html",
    ]:
        src = WEB_SRC / name
        if src.exists():
            shutil.copy2(src, dest / name)
    src_dir = dest / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    for name in ["App.jsx", "auth.js", "main.jsx", "styles.css"]:
        shutil.copy2(WEB_SRC / "src" / name, src_dir / name)


CHANGELOG = {
    1: "START — first deployable CDK app (SSM parameter only).",
    2: "ADD Cognito User Pool (`UserPool`).",
    3: "ADD SPA app client (`SpaClient`) with USER_PASSWORD_AUTH.",
    4: "ADD demo user custom resources + DemoUsername/DemoPassword outputs.",
    5: "ADD private S3 `UiBucket`.",
    6: "ADD CloudFront + OAC + placeholder index.html deploy.",
    7: "ADD `web/` React app + BucketDeployment of login UI (`chatEnabled: false`).",
    8: "ADD `api/` FastAPI health + App Runner + CF `/health` and `/api/*` behaviors.",
    9: "ADD JWT verification in API + Cognito env on App Runner (`AUTH_DISABLED=false`).",
    10: "ADD AgentCore invoke IAM + SUPPORT_RUNTIME_ARN + `chatEnabled: true`.",
}


def step_readme(step: int, folder: str, title: str) -> str:
    prev = STEPS[step - 2][0] if step > 1 else None
    nxt = STEPS[step][0] if step < 10 else None
    show = {
        1: "CloudFormation stack exists; output `DeployStep=1`.",
        2: "Cognito console → `lauki-support-users`.",
        3: "App client `lauki-support-spa` on the pool.",
        4: "User `demo` exists. Outputs show password.",
        5: "S3 bucket name in outputs.",
        6: "Open `CloudFrontUrl` → placeholder HTML.",
        7: "Open `CloudFrontUrl` → login as demo / DemoUser1! (chat locked).",
        8: "`curl $CloudFrontUrl/health` → ok.",
        9: "`curl $CloudFrontUrl/api/me` → 401 without token.",
        10: "Login → ask about SIM activation → full answer.",
    }[step]
    runtime = ""
    if step == 10:
        runtime = "export SUPPORT_RUNTIME_ARN='arn:aws:bedrock-agentcore:...'\n"
    diff_hint = ""
    if prev:
        diff_hint = f"""
## See the delta vs previous folder

```bash
diff -ru ../{prev} . | less
# or in Cursor: open ../{prev}/cdk/stack.py and ./cdk/stack.py side-by-side
```
"""
    next_hint = f"\n**Next:** `../{nxt}/`\n" if nxt else "\n**Done — full stack.**\n"

    return f"""# Step {step:02d} — {title}

Folder: `{folder}`

## Deploy

```bash
cd 06.progressive-deploy/{folder}
{runtime}bash deploy.sh
```

## Verify

{show}
{diff_hint}
## What changed vs previous

{CHANGELOG[step]}
{next_hint}
Same CloudFormation stack name: **`LaukiSupportStack`**  
(so step N updates what step N-1 deployed — do not run two folders against different accounts in parallel on the same stack).
"""


def main() -> None:
    # wipe old generated folders (keep _generate.py and README)
    for child in ROOT.iterdir():
        if child.is_dir() and child.name[:2].isdigit():
            shutil.rmtree(child)

    for i, (folder, title) in enumerate(STEPS, start=1):
        step_dir = ROOT / folder
        cdk_dir = step_dir / "cdk"
        cdk_dir.mkdir(parents=True)

        (cdk_dir / "cdk.json").write_text(CDK_JSON)
        (cdk_dir / "requirements.txt").write_text(REQUIREMENTS)
        (cdk_dir / "app.py").write_text(app_py(needs_runtime=(i == 10)))
        (cdk_dir / "stack.py").write_text(build_stack(i))

        deploy = step_dir / "deploy.sh"
        deploy.write_text(deploy_sh(i, needs_runtime=(i == 10)))
        deploy.chmod(0o755)

        (step_dir / "README.md").write_text(step_readme(i, folder, title))
        (step_dir / "WHAT_CHANGED.md").write_text(
            f"# What changed in step {i:02d}\n\n{CHANGELOG[i]}\n"
        )

        if i >= 7:
            copy_web(step_dir / "web")
        if i >= 8:
            api = step_dir / "api"
            api.mkdir(parents=True)
            (api / "main.py").write_text(api_main(i))
            (api / "requirements.txt").write_text(api_requirements(i))
            shutil.copy2(LAB / "api" / "Dockerfile", api / "Dockerfile")

        print(f"wrote {folder}")

    index = ROOT / "README.md"
    index.write_text(
        """# Classroom steps — 10 folders, cumulative code

Each folder is a **complete, runnable snapshot**. Code only grows; nothing is removed.

```
01_empty_cdk          → deploy
02_cognito_pool       → 01 + Cognito pool
03_cognito_client     → 02 + SPA client
04_demo_user          → 03 + demo user
05_s3_ui_bucket       → 04 + S3
06_cloudfront         → 05 + CloudFront placeholder
07_react_login        → 06 + React login (chat off)
08_apprunner_health   → 07 + FastAPI /health
09_jwt_lock           → 08 + JWT /api/me
10_agentcore_chat     → 09 + AgentCore chat (full)
```

## How to teach

1. Open `01_empty_cdk` and `02_cognito_pool` side-by-side in the IDE.
2. Deploy folder 01: `bash deploy.sh`
3. Show students the delta in folder 02 (`cdk/stack.py`).
4. Deploy folder 02 (updates the **same** stack — set `STACK_NAME` to choose it).
5. Repeat through 10.

```bash
export STACK_NAME=LaukiSupportClassA   # new name = new stack; omit for LaukiSupportStack
cd 06.progressive-deploy/01_empty_cdk && bash deploy.sh
cd ../02_cognito_pool && bash deploy.sh
# ...
export SUPPORT_RUNTIME_ARN='arn:...'
cd ../10_agentcore_chat && bash deploy.sh
```

## Diff any two steps

```bash
diff -ru 07_react_login 08_apprunner_health | less
```

## Regenerate folders

If you change the lab’s `web/` or `api/`, refresh copies:

```bash
python3 06.progressive-deploy/_generate.py
```

## Note vs `cdk/` staged `-c stage=N`

The parent `cdk/` app uses one codebase with stage flags.  
**These folders** are for live teaching — each directory is the whole truth for that moment.
"""
    )
    print("done →", ROOT)


if __name__ == "__main__":
    main()
