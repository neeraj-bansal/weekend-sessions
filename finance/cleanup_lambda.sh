#!/usr/bin/env bash
# Cleanup Finance Agent AWS Lambda stack created by AWS SAM
set -euo pipefail

STACK_NAME="finance-fundamental-analyst"
REGION="${AWS_REGION:-us-east-1}"

echo "================================================================="
echo " Deleting AWS Lambda Serverless Stack: ${STACK_NAME}"
echo " Region: ${REGION}"
echo "================================================================="

sam delete \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --no-prompts

echo "✅ Stack ${STACK_NAME} deleted successfully!"
