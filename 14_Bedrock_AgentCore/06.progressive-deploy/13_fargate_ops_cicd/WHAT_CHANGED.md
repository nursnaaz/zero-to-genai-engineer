# What changed in step 13 (vs step 12)

ADD ECS service auto scaling (min=1, max=3, requests-per-target=10) via
`scale_on_request_count` + optional monthly cost budget with email alert +
GitHub Actions OIDC deploy role (reuses the existing OIDC provider from
11_ops_cicd instead of creating a duplicate).
