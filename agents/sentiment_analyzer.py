"""Sentiment Analysis Agent – analyses response quality and predicts satisfaction.

Returns a sentiment score and recommendation (deliver / refine / escalate).
"""

from __future__ import annotations

import json
from typing import Any, Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

import config


_SYSTEM_PROMPT = """You are a sentiment and satisfaction analysis engine.
Given a customer query and the agent's proposed response, evaluate:

1. How well the response addresses the customer's concern (0-1)
2. The predicted customer satisfaction level (high / low / unknown)
3. Whether the response should be delivered as-is, refined, or escalated to a human.

Respond ONLY with a JSON object:
{
  "sentiment_score": <float 0-1>,
  "satisfaction_level": "high" | "low" | "unknown",
  "action": "deliver" | "refine" | "escalate",
  "refinement_suggestion": "<optional suggestion if action is refine>"
}
"""


def analyze(user_query: str, agent_response: str) -> Dict[str, Any]:
    """Analyze sentiment and predicted satisfaction."""

    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.0,
    )

    response = llm.invoke(
        [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(
                content=f"CUSTOMER QUERY:\n{user_query}\n\nAGENT RESPONSE:\n{agent_response}"
            ),
        ]
    )

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        text = response.content
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(text[start:end])
        else:
            result = {
                "sentiment_score": 0.5,
                "satisfaction_level": "unknown",
                "action": "deliver",
                "refinement_suggestion": "",
            }

    return {
        "sentiment_score": float(result.get("sentiment_score", 0.5)),
        "satisfaction_level": result.get("satisfaction_level", "unknown"),
        "action": result.get("action", "deliver"),
        "refinement_suggestion": result.get("refinement_suggestion", ""),
    }


def refine_response(user_query: str, original_response: str, suggestion: str) -> str:
    """Refine an agent response based on a sentiment suggestion."""

    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.4,
    )

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a response refinement agent. Improve the given response "
                    "based on the improvement suggestion provided. Make the response more "
                    "empathetic, clear, and helpful while keeping it accurate."
                )
            ),
            HumanMessage(
                content=(
                    f"CUSTOMER QUERY:\n{user_query}\n\n"
                    f"ORIGINAL RESPONSE:\n{original_response}\n\n"
                    f"IMPROVEMENT SUGGESTION:\n{suggestion}\n\n"
                    "Please provide the refined response:"
                )
            ),
        ]
    )

    return response.content
