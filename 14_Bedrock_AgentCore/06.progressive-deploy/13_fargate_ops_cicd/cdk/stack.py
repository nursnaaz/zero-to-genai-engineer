from __future__ import annotations

from typing import Any

import aws_cdk as cdk
from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_cognito as cognito
from aws_cdk import custom_resources as cr
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3_deployment as s3deploy
from pathlib import Path
from aws_cdk import aws_budgets as budgets
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_iam as iam
from constructs import Construct

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "api"
WEB_DIR = ROOT / "web"

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "DemoUser1!"


class LaukiSupportFargateStack(Stack):
    """Same app as 10_agentcore_chat, on ECS Fargate + ALB instead of App Runner.

    A separate, independent stack (own Cognito pool, own S3/CloudFront, own
    compute) — nothing here is shared with `LaukiSupportStack`. Safe to
    deploy or delete without touching the App Runner demo.

    Cost note: uses `nat_gateways=0` and runs the Fargate task in a PUBLIC
    subnet with a public IP, specifically to avoid a NAT Gateway's ~$32/mo
    fixed cost for what is a classroom comparison, not a production setup.
    In a real deployment you'd put the task in a private subnet behind a
    NAT Gateway (or VPC endpoints) instead of giving it a public IP.
    """

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

        _safe = "".join(
            ch.lower() if ch.isalnum() else "-" for ch in construct_id
        ).strip("-")[:24]

        CfnOutput(self, "DeployStep", value="13-fargate-ops")
        CfnOutput(
            self,
            "StepHint",
            value="Fargate app (step 12) + ECS request-count autoscaling + cost budget + GitHub Actions deploy role",
        )
        CfnOutput(self, "StackName", value=construct_id)

        ssm.StringParameter(
            self,
            "StageMarker",
            parameter_name=f"/lauki-support/{_safe}/deploy-stage",
            string_value="13-fargate-ops",
            description="Classroom step folder (Fargate alternative)",
        )

        # ----- Cognito (same shape as step 10) -----
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
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
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

        # ----- S3 bucket for the React UI (same shape as step 10) -----
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

        # ----- VPC — no NAT Gateway (cost), task runs in a public subnet -----
        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                )
            ],
        )

        cluster = ecs.Cluster(self, "Cluster", vpc=vpc, container_insights=False)

        api_image = ecr_assets.DockerImageAsset(
            self,
            "ApiImage",
            directory=str(API_DIR),
            platform=ecr_assets.Platform.LINUX_AMD64,
            asset_name="lauki-support-api",
        )

        task_role = iam.Role(
            self,
            "FargateTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        endpoint_arn = f"{support_runtime_arn}/runtime-endpoint/DEFAULT"
        task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agentcore:InvokeAgentRuntime",
                    "bedrock-agentcore:InvokeAgentRuntimeForUser",
                ],
                resources=[support_runtime_arn, endpoint_arn],
            )
        )
        CfnOutput(self, "SupportRuntimeArn", value=support_runtime_arn)

        # ----- Fargate service + its own Application Load Balancer -----
        # This one L2 construct is the Fargate equivalent of App Runner's
        # single CfnService: it wires up the task definition, ECS service,
        # ALB, target group, and listener together.
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ApiService",
            cluster=cluster,
            cpu=1024,
            memory_limit_mib=2048,
            desired_count=1,
            assign_public_ip=True,  # no NAT Gateway, so the task needs its own public IP
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            public_load_balancer=True,
            listener_port=80,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_docker_image_asset(api_image),
                container_port=8000,
                task_role=task_role,
                environment={
                    "AWS_REGION": region,
                    "CORS_ORIGINS": "*",
                    "COGNITO_REGION": region,
                    "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
                    "COGNITO_CLIENT_ID": user_pool_client.user_pool_client_id,
                    "AUTH_DISABLED": "false",
                    "SUPPORT_RUNTIME_ARN": support_runtime_arn,
                },
            ),
        )
        # Same /health path App Runner used; Fargate/ALB needs it configured
        # explicitly on the target group (App Runner had this built in).
        fargate_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200",
            interval=Duration.seconds(15),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=5,
        )
        # Demo-only: ALB accepts HTTP from anywhere so CloudFront can reach
        # it. In production, restrict this security group to CloudFront's
        # `com.amazonaws.global.cloudfront.origin-facing` managed prefix
        # list instead of 0.0.0.0/0.
        CfnOutput(
            self,
            "AlbUrl",
            value=f"http://{fargate_service.load_balancer.load_balancer_dns_name}",
        )

        # ----- CloudFront (same shape as step 10, ALB origin instead of App Runner) -----
        oac = cloudfront.S3OriginAccessControl(
            self, "UiOac", signing=cloudfront.Signing.SIGV4_ALWAYS
        )
        s3_origin = origins.S3BucketOrigin.with_origin_access_control(
            ui_bucket, origin_access_control=oac
        )
        api_origin = origins.LoadBalancerV2Origin(
            fargate_service.load_balancer,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
        )
        api_behavior = cloudfront.BehaviorOptions(
            origin=api_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
            cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        )
        additional = {"/api/*": api_behavior, "/health": api_behavior}

        distribution = cloudfront.Distribution(
            self,
            "UiDistribution",
            comment="lauki-support-ui-fargate",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                compress=True,
            ),
            additional_behaviors=additional,
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

        config = {
            "step": "13-fargate-ops",
            "stage": "13-fargate-ops",
            "authRequired": True,
            "chatEnabled": True,
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

        # ----- Step 13: ECS service auto scaling (Fargate's equivalent of -----
        # ----- App Runner's CfnAutoScalingConfiguration from step 11)     -----
        # App Runner scales on "requests per instance"; the closest native
        # ECS/ALB equivalent is ALB request-count-per-target, which is what
        # scale_on_request_count() wires up under the hood (an Application
        # Auto Scaling policy on the ECS service, driven by the same ALB
        # metric App Runner uses internally).
        min_capacity, max_capacity, requests_per_target = 1, 3, 5
        scaling = fargate_service.service.auto_scale_task_count(
            min_capacity=min_capacity, max_capacity=max_capacity
        )
        scaling.scale_on_request_count(
            "RequestCountScaling",
            requests_per_target=requests_per_target,
            target_group=fargate_service.target_group,
        )
        CfnOutput(
            self,
            "AutoScalingLimits",
            value=(
                f"min={min_capacity} max={max_capacity} "
                f"requests_per_target={requests_per_target} (edit in stack.py)"
            ),
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

        # ----- Step 13: let GitHub Actions deploy this stack via OIDC -----
        # Only one OIDC provider per URL is allowed per AWS account — the
        # App Runner ops-day stack (11_ops_cicd) already created one, so
        # this imports it by ARN instead of creating a duplicate (deploy.sh
        # auto-detects it; see that folder's role for the precedent).
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
