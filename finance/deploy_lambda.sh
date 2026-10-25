#!/usr/bin/env bash
# Deploy Finance Agent to AWS Lambda via AWS SAM CLI
set -euo pipefail

STACK_NAME="finance-fundamental-analyst"
REGION="${AWS_REGION:-us-east-1}"
BEDROCK_MODEL="${BEDROCK_MODEL_ID:-us.amazon.nova-2-lite-v1:0}"

# Configure Docker socket for Colima if applicable
if [ -S "$HOME/.colima/default/docker.sock" ] && [ -z "${DOCKER_HOST:-}" ]; then
    export DOCKER_HOST="unix://$HOME/.colima/default/docker.sock"
fi

# Detect architecture (arm64 for Apple Silicon / Graviton, x86_64 otherwise)
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    SAM_ARCH="arm64"
else
    SAM_ARCH="x86_64"
fi

echo "================================================================="
echo " Deploying Finance Agent to AWS Lambda (${SAM_ARCH})"
echo " Stack:  ${STACK_NAME}"
echo " Region: ${REGION}"
echo " Model:  ${BEDROCK_MODEL}"
echo "================================================================="

# Build SAM application
sam build --template template.yaml

# Deploy SAM application
sam deploy \
    --stack-name "${STACK_NAME}" \
    --resolve-s3 \
    --resolve-image-repos \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides Architecture="${SAM_ARCH}" BedrockModelId="${BEDROCK_MODEL}" \
    --region "${REGION}" \
    --no-confirm-changeset

echo ""
echo "✅ Lambda deployment complete!"
echo "Retrieve your API endpoint from the stack outputs above."
