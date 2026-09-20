from __future__ import annotations

from typing import Any

import aws_cdk as cdk
from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_cognito as cognito
from aws_cdk import custom_resources as cr
from aws_cdk import aws_s3 as s3
from aws_cdk import Duration
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3_deployment as s3deploy
from pathlib import Path
from aws_cdk import aws_apprunner as apprunner
from aws_cdk import aws_budgets as budgets
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_iam as iam
from constructs import Construct

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "api"
WEB_DIR = ROOT / "web"

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "DemoUser1!"

class LaukiSupportStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        support_runtime_arn: str,
        budget_alert_email: str = "",
        budget_limit_usd: float = 15.0,
        github_repo: str = "nursnaaz/zero-to-genai-engineer",
        github_oidc_provider_arn: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        region = Stack.of(self).region

        # Unique per STACK_NAME so parallel classroom stacks do not collide
        _safe = "".join(
            ch.lower() if ch.isalnum() else "-" for ch in construct_id
        ).strip("-")[:24]
        CfnOutput(self, "DeployStep", value="11")
        CfnOutput(
            self,
            "StepHint",
            value="Ops day — auto scaling + cost budget + GitHub Actions deploy role",
        )
        CfnOutput(self, "StackName", value=construct_id)

        ssm.StringParameter(
            self,
            "StageMarker",
            parameter_name=f"/lauki-support/{_safe}/deploy-stage",
            string_value="11",
            description="Classroom step folder",
        )


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

        api_service = apprunner.CfnService(
            self,
            "ApiService",
            service_name=f"lauki-api-{_safe}"[:40],
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
            value=f"https://{api_service.attr_service_url}",
        )


        oac = cloudfront.S3OriginAccessControl(
            self,
            "UiOac",
            signing=cloudfront.Signing.SIGV4_ALWAYS,
        )
        s3_origin = origins.S3BucketOrigin.with_origin_access_control(
            ui_bucket,
            origin_access_control=oac,
        )
        additional: dict[str, cloudfront.BehaviorOptions] = {}

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
            value=f"https://{distribution.distribution_domain_name}",
        )


        chat_enabled = True
        config = {
            "step": 11,
            "stage": 11,
            "authRequired": True,
            "chatEnabled": chat_enabled,
            "region": region,
            "apiBase": "",
            "userPoolId": user_pool.user_pool_id,
            "clientId": user_pool_client.user_pool_client_id,
        }
        web_asset = s3deploy.Source.asset(
            str(WEB_DIR),
            exclude=["node_modules", "dist", ".git"],
            bundling=cdk.BundlingOptions(
                image=cdk.DockerImage.from_registry(
                    "public.ecr.aws/docker/library/node:20-alpine"
                ),
                user="root",
                environment={"VITE_API_BASE": ""},
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

        # ----- Step 11: App Runner auto scaling + a monthly cost budget -----
        # min_size keeps one warm instance (no cold start on the first
        # request); max_size is a hard ceiling so a traffic burst in class
        # can't turn into a runaway bill; max_concurrency is how many
        # in-flight requests one instance takes before App Runner starts a
        # new one.
        min_size, max_size, max_concurrency = 1, 3, 15
        autoscaling = apprunner.CfnAutoScalingConfiguration(
            self,
            "ApiAutoScaling",
            auto_scaling_configuration_name=f"lauki-support-{_safe}"[:32],
            min_size=min_size,
            max_size=max_size,
            max_concurrency=max_concurrency,
        )
        api_service.auto_scaling_configuration_arn = (
            autoscaling.attr_auto_scaling_configuration_arn
        )
        CfnOutput(
            self,
            "AutoScalingLimits",
            value=f"min={min_size} max={max_size} concurrency={max_concurrency} (edit in stack.py)",
        )

        # Budgets supports an EMAIL subscriber directly — no SNS topic or
        # topic policy needed, which keeps this safe to run live.
        if budget_alert_email:
            budgets.CfnBudget(
                self,
                "MonthlyCostBudget",
                budget=budgets.CfnBudget.BudgetDataProperty(
                    budget_type="COST",
                    time_unit="MONTHLY",
                    budget_limit=budgets.CfnBudget.SpendProperty(
                        amount=budget_limit_usd, unit="USD"
                    ),
                ),
                notifications_with_subscribers=[
                    budgets.CfnBudget.NotificationWithSubscribersProperty(
                        notification=budgets.CfnBudget.NotificationProperty(
                            notification_type="ACTUAL",
                            comparison_operator="GREATER_THAN",
                            threshold=80,
                            threshold_type="PERCENTAGE",
                        ),
                        subscribers=[
                            budgets.CfnBudget.SubscriberProperty(
                                subscription_type="EMAIL",
                                address=budget_alert_email,
                            )
                        ],
                    )
                ],
            )
            CfnOutput(
                self,
                "BudgetAlert",
                value=f"${budget_limit_usd}/mo, alert at 80% -> {budget_alert_email}",
            )

        # ----- Step 11: let GitHub Actions deploy this stack via OIDC -----
        # (no long-lived AWS keys stored in the repo — same "no secrets in
        # the browser" idea from the Cognito/App Runner design, applied to
        # the pipeline instead of the UI.)
        if github_oidc_provider_arn:
            oidc_provider = iam.OpenIdConnectProvider.from_open_id_connect_provider_arn(
                self, "GithubOidcProvider", github_oidc_provider_arn
            )
        else:
            oidc_provider = iam.OpenIdConnectProvider(
                self,
                "GithubOidcProvider",
                url="https://token.actions.githubusercontent.com",
                client_ids=["sts.amazonaws.com"],
            )

        deploy_role = iam.Role(
            self,
            "GithubActionsDeployRole",
            assumed_by=iam.WebIdentityPrincipal(
                oidc_provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{github_repo}:*"
                    },
                },
            ),
            # Classroom scope: broad enough to deploy this whole stack.
            # Tighten to a scoped CDK-deploy policy once the pipeline is
            # proven — see OPS_DAY_RUNBOOK.md.
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
            ],
            max_session_duration=Duration.hours(1),
        )
        CfnOutput(self, "GithubActionsDeployRoleArn", value=deploy_role.role_arn)
