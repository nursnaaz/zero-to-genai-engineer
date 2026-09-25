# Bedrock AgentCore labs

Self-contained labs for Amazon Bedrock AgentCore. Each Runtime lab starts from an
**empty** AgentCore account: create your own Memory → Gateway → Identity, then deploy.

| Lab | Framework | Flagship | Follow |
|---|---|---|---|
| [`01.langraph-agentcore-bedrock`](./01.langraph-agentcore-bedrock/) | LangGraph | Research + Streamlit (+ Harness) | Steps 0→3, Demos 1–7 |
| [`02.strands-agentcore-bedrock`](./02.strands-agentcore-bedrock/) | Strands | Support Copilot + Streamlit | Steps 0→3, Demos 1–5 |
| [`03.crewai-agentcore-bedrock`](./03.crewai-agentcore-bedrock/) | CrewAI | Competitor Brief + Streamlit | Steps 0→3, Demos 1–5 |
| [`04.framework-power-agents`](./04.framework-power-agents/) | **All three** | Side-by-side power-agent notebook | Open `powerful_agents_comparison.ipynb` |
| [`05.agentcore-production-deploy`](./05.agentcore-production-deploy/) | Strands + React | Cognito → CloudFront/S3 UI → App Runner API → AgentCore + Guardrail | See lab README |
| [`06.progressive-deploy`](./06.progressive-deploy/) | Same app as lab 05 | 01→10 product path + optional 11 ops/CI + 12/13 Fargate alternative — taught as folders instead of stage flags | See lab README |

## Shared student rules (01–03)

1. Do **not** copy someone else’s `MEMORY_ID`, Gateway credentials, or Runtime ARN.
2. Regions: Memory / Runtime / Identity = **`us-east-1`**; Gateway + Cognito = **`us-west-2`**.
3. Prefer **`agentcore deploy`** (old name: `launch`). Pass secrets with `--env` (Runtime ignores `.env`).
4. Create Gateway with that lab’s `scripts/create_mcp_gateway.py` → local `gateway-credentials.json`.
5. After Memory / Identity / Browser agents: run that lab’s IAM grant script on the Runtime role.

Recommended order: **04 (compare locally)** → **01 → 02 → 03** (deploy the same ideas on AgentCore) → **05 or 06** (ship lab 02's agent to production on your own AWS account — pick one path, or do both).
You can also run **02 or 03 alone** — each README is from scratch.
