# What changed vs step 10

SWAP compute: `apprunner.CfnService` -> VPC + ECS Cluster + Fargate Service
+ Application Load Balancer (`ecs_patterns.ApplicationLoadBalancedFargateService`).
Everything else (Cognito, S3, CloudFront, the Docker image, the React UI)
is unchanged. Independent stack — does not touch `LaukiSupportStack`.
