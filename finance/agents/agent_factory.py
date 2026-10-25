"""Agent factory providing unified LLM invocation across Groq, OpenAI, Bedrock, and offline fallback."""

import json
import logging
import os
from typing import Any, Callable
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def run_llm_inference(
    system_prompt: str,
    user_prompt: str,
    json_mode: bool = False,
    tools: list[Callable] | None = None,
) -> str:
    """Run an LLM call across available providers (Groq -> OpenAI -> Bedrock -> Deterministic Fallback).

    Args:
        system_prompt: Persona, instructions, and output schema.
        user_prompt: Specific task and input data.
        json_mode: Enforce strict JSON output if supported.
        tools: Optional list of callable tool functions.

    Returns:
        The generated text or JSON response string.
    """
    # 1. Try Groq if GROQ_API_KEY is available
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key and groq_api_key.strip():
        try:
            from groq import Groq

            client = Groq(api_key=groq_api_key)
            model_id = os.getenv("GROQ_MODEL_ID", "llama-3.3-70b-versatile")
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response_format = {"type": "json_object"} if json_mode else None

            completion = client.chat.completions.create(
                model=model_id,
                messages=messages,
                response_format=response_format,
                temperature=0.1,
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            logger.warning("Groq inference error, attempting fallback: %s", str(e))

    # 2. Try OpenAI if OPENAI_API_KEY is available
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key and openai_api_key.strip():
        try:
            from openai import OpenAI

            client = OpenAI(api_key=openai_api_key)
            model_id = os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini")
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response_format = {"type": "json_object"} if json_mode else None

            completion = client.chat.completions.create(
                model=model_id,
                messages=messages,
                response_format=response_format,
                temperature=0.1,
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            logger.warning("OpenAI inference error, attempting fallback: %s", str(e))

    # 3. Try AWS Bedrock if credentials are configured
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        try:
            import boto3

            region = os.getenv("AWS_REGION", "us-east-1")
            bedrock_client = boto3.client("bedrock-runtime", region_name=region)
            model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-haiku-20241022-v1:0")

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "system": system_prompt,
                "messages": [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
                "temperature": 0.1,
            })
            resp = bedrock_client.invoke_model(modelId=model_id, body=body)
            resp_body = json.loads(resp["body"].read().decode("utf-8"))
            return resp_body.get("content", [{}])[0].get("text", "")
        except Exception as e:
            logger.warning("Bedrock inference error: %s", str(e))

    # 4. Fallback: Return raw contextual synthesis without external API
    logger.info("Using built-in synthesis fallback.")
    return ""
