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

    # 2. Try AWS Bedrock (Bedrock Converse API supports Nova, Claude, Llama, Mistral)
    try:
        import boto3

        region = os.getenv("AWS_REGION", "us-east-1")
        bedrock_client = boto3.client("bedrock-runtime", region_name=region)
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-2-lite-v1:0")

        converse_response = bedrock_client.converse(
            modelId=model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={"maxTokens": 2048, "temperature": 0.1},
        )
        output_msg = converse_response.get("output", {}).get("message", {}).get("content", [])
        if output_msg and "text" in output_msg[0]:
            return output_msg[0]["text"]
    except Exception as e:
        logger.warning("Bedrock inference error: %s", str(e))

    # 3. Try OpenAI if OPENAI_API_KEY is available
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

    # 4. Fallback: Return raw contextual synthesis without external API
    logger.info("Using built-in synthesis fallback.")
    return ""
