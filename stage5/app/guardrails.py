import os
import json
import boto3
from typing import Optional

GUARDRAIL_ID = os.getenv("GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.getenv("GUARDRAIL_VERSION", "1")
GUARDRAILS_ENABLED = os.getenv("GUARDRAILS_ENABLED", "false").lower() == "true"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

class GuardrailBlocked(Exception):
    def __init__(self, message: str, action: str = "BLOCKED"):
        self.message = message
        self.action = action
        super().__init__(message)

def apply_guardrail(text: str, source: str = "INPUT") -> str:
    """
    Apply Bedrock Guardrail to text.
    source: "INPUT" for user queries, "OUTPUT" for model responses
    Returns cleaned text or raises GuardrailBlocked if policy violated.
    """
    if not GUARDRAILS_ENABLED or not GUARDRAIL_ID:
        return text

    try:
        client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        response = client.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source=source,
            content=[{"text": {"text": text}}]
        )

        action = response.get("action", "NONE")
        
        if action == "GUARDRAIL_INTERVENED":
            # Check what was blocked
            assessments = response.get("assessments", [])
            blocked_topics = []
            for assessment in assessments:
                topic_policy = assessment.get("topicPolicy", {})
                for topic in topic_policy.get("topics", []):
                    if topic.get("action") == "BLOCKED":
                        blocked_topics.append(topic.get("name", "unknown"))
                
                content_policy = assessment.get("contentPolicy", {})
                for filter_result in content_policy.get("filters", []):
                    if filter_result.get("action") == "BLOCKED":
                        blocked_topics.append(filter_result.get("type", "unknown"))

            blocked_msg = response.get(
                "blockedResponse",
                "I cannot process this request as it violates content policies."
            )
            raise GuardrailBlocked(blocked_msg, action)

        # Return cleaned output (PII anonymized etc)
        outputs = response.get("outputs", [])
        if outputs:
            return outputs[0].get("text", text)
        return text

    except GuardrailBlocked:
        raise
    except Exception as e:
        print(f"Guardrail error: {e}")
        return text  # Fail open - return original if guardrail errors

def check_input(text: str) -> str:
    """Apply guardrail to user input before processing."""
    return apply_guardrail(text, "INPUT")

def check_output(text: str) -> str:
    """Apply guardrail to model output before returning to user."""
    return apply_guardrail(text, "OUTPUT")
