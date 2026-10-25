# ☁️ Cloud Deployment Guide: Shipping the Finance Agent to Production

This guide prepares the **60-Second Multi-Agent Fundamental Stock Analyst** for cloud deployment across the three patterns taught in **Section 6**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        3 CLOUD DEPLOYMENT TARGETS                      │
├───────────────────┬────────────────────────────┬───────────────────────┤
│ Target A:         │ Target B:                  │ Target C:             │
│ Bedrock AgentCore │ Amazon ECS on Fargate      │ AWS Lambda + API GW   │
│ (Managed Runtime) │ (Containerized Service)    │ (Serverless Endpoint) │
└───────────────────┴────────────────────────────┴───────────────────────┘
```

---

## 🎯 Target Comparison

| Feature | 1. AWS Lambda | 2. ECS Fargate | 3. Bedrock AgentCore Runtime |
|---|---|---|---|
| **Architecture** | Serverless function per request | Always-on Docker container | Managed Agent MicroVM runtime |
| **Max Run Time** | 15 mins (API Gateway: 29s timeout) | Unlimited | Up to 8 hours per session |
| **Operational Overhead** | Low (Packaging & handler) | Medium (ALB, Task Definition, VPC) | Minimal (Agent code & AgentCore CLI) |
| **Best Used For** | Short, event-driven API queries | Always-on web apps / internal dashboards | Long-running, multi-agent A2A & MCP flows |

---

## 🚀 Target 1: Amazon Bedrock AgentCore Runtime (Section 6 Native)

Bedrock AgentCore provides a fully managed runtime for Strands agents with built-in memory and MCP tool support.

### Deployment Steps
1. Install the starter toolkit:
   ```bash
   pip install bedrock-agentcore-starter-toolkit
   ```
2. Configure credentials in `.env` or shell:
   ```bash
   export AWS_PROFILE=<your-profile>
   export AWS_REGION=us-east-1
   export BEDROCK_MODEL_ID=us.amazon.nova-2-lite-v1:0  # or claude-sonnet-4-6
   ```
3. Deploy the agent package:
   ```bash
   agentcore deploy --entrypoint finance/main.py --env BEDROCK_MODEL_ID=$BEDROCK_MODEL_ID
   ```

---

## 🐳 Target 2: Containerized Deployment on Amazon ECS Fargate

Deploy the FastAPI service ([`app.py`](app.py)) as a microservice on AWS Fargate behind an Application Load Balancer (ALB).

### 1. Security-Hardened Dockerfile (`Dockerfile`)

```dockerfile
FROM registry.redhat.io/ubi9/python-311-minimal:latest

# Create non-root application user
RUN useradd -m -u 1001 appuser

WORKDIR /app

# Copy dependency definitions
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn

# Copy application code
COPY --chown=appuser:appuser . .

USER 1001

EXPOSE 8000

CMD ["uvicorn", "finance.app:app", "--host", "127.0.0.1", "--port", "8000"]
```

### 2. Run Container Locally
```bash
docker build -t finance-agent:latest -f Dockerfile .
docker run -p 8000:8000 finance-agent:latest
```

### 3. Test REST Endpoints
```bash
# Health check
curl http://127.0.0.1:8000/health

# Run Fundamental Analysis
curl -X POST http://127.0.0.1:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"ticker": "AAPL"}'
```

---

## ⚡ Target 3: Serverless AWS Lambda + API Gateway

The dedicated serverless stack is defined in [`template.yaml`](template.yaml), [`lambda_handler.py`](lambda_handler.py), and [`deploy_lambda.sh`](deploy_lambda.sh).

### 1. Serverless Architecture
```
User / Web App ──(HTTPS POST)──> Amazon API Gateway (/analyze) ──> AWS Lambda (Container Image) ──> Bedrock & Data APIs
```

### 2. Deploy via AWS SAM CLI
```bash
cd weekend-sessions-main/finance
./deploy_lambda.sh
```

### 3. Test Live API Gateway Endpoint
```bash
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/analyze \
     -H "Content-Type: application/json" \
     -d '{"ticker": "AAPL"}'
```
