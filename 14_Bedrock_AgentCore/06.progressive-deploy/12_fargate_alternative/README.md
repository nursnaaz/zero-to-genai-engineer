# Step 12 (alternative) — same app, ECS Fargate + ALB instead of App Runner

Folder: `12_fargate_alternative`

Independent stack — default name `LaukiSupportFargateStack`, its own
Cognito pool, S3 bucket, CloudFront distribution, VPC, and compute. Does
**not** touch `LaukiSupportStack` (the App Runner demo from step 10/11).
Safe to deploy and `cdk destroy` on its own.

## Why this exists

"Can you convert App Runner to Fargate?" — yes, and this is what it costs
in code and infrastructure to do it. Compare `stack.py` here against
[`../10_agentcore_chat/cdk/stack.py`](../10_agentcore_chat/cdk/stack.py):
same Cognito, same S3/CloudFront, same Docker image — the only thing that
changed is the compute block.

| | App Runner (step 10) | Fargate (this folder) |
|---|---|---|
| Compute resource | 1 `apprunner.CfnService` | VPC + ECS Cluster + Task Definition + Service + ALB + target group (`ecs_patterns.ApplicationLoadBalancedFargateService` bundles most of this) |
| Load balancing / TLS | Built in | You own the ALB |
| Health checks | Built-in property | Configured explicitly on the target group |
| Autoscaling | `apprunner.CfnAutoScalingConfiguration` (see step 11) | Application Auto Scaling on the ECS service (not added here — out of scope for this comparison) |
| Networking | No VPC needed | Needs a VPC — this demo uses `nat_gateways=0` + a public subnet + public IP on the task to avoid a ~$32/mo NAT Gateway. A real deployment would use private subnets + NAT (or VPC endpoints) instead. |
| Always-on cost | Pay for provisioned/active vCPU+memory | Same, **plus** the ALB (~$16-20/mo whether or not it's used) |

**The lesson for class:** App Runner traded control for simplicity — one
resource instead of six. Fargate is what you reach for when you need that
control back (custom networking, sidecars, non-HTTP protocols, more
scaling signals) — but you're now the one operating the load balancer.

## Deploy

```bash
cd 06.progressive-deploy/12_fargate_alternative
export SUPPORT_RUNTIME_ARN='arn:aws:bedrock-agentcore:...'
bash deploy.sh
```

## Verify

```bash
aws cloudformation describe-stacks --stack-name LaukiSupportFargateStack --region us-east-1 \
  --query "Stacks[0].Outputs"
```

Login → ask about SIM activation → full answer, same as step 10.

## Cleanup

```bash
cd cdk && source .venv/bin/activate
npx cdk destroy LaukiSupportFargateStack -c stackName=LaukiSupportFargateStack -c supportRuntimeArn=unused
```

This is a fully separate stack — destroying it has no effect on
`LaukiSupportStack`.
