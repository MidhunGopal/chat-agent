"""Intent Router Agent – NLP Processing & Intent Classification.

Uses OpenAI to classify the customer/agent query into one of:
  new_application | underwriting_status | policy_query | general_info | document_upload
"""

from __future__ import annotations

import json
from typing import Any, Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

import config


_SYSTEM_PROMPT = """You are an intent classification engine for an insurance company.
Given a customer or agent query, classify the intent into exactly ONE of these categories:

1. new_application     – The user wants to start, check, or modify an insurance application.
2. underwriting_status – The user is asking about underwriting progress, risk assessment, or approval status.
3. policy_query        – The user is asking about an existing policy: coverage, claims, renewal, cancellation, premium, etc.
4. general_info        – General insurance questions, FAQs, company info, product info.
5. document_upload     – The user wants to upload, submit, or process a document (e.g. ID, medical report).
6. out_of_scope        – The query is NOT related to insurance, policies, applications, claims, or any financial/insurance product. Examples: weather, traffic, sports, recipes, general chit-chat unrelated to insurance.

IMPORTANT: If the query has nothing to do with insurance, financial products, policies, applications, claims, underwriting, or company services, you MUST classify it as "out_of_scope".

Respond ONLY with a JSON object having these keys:
  "intent": one of the 6 categories above,
  "confidence": float between 0 and 1,
  "entities": dict of any extracted entities (policy_id, application_id, name, etc.)

Do NOT include any other text.
"""


def classify_intent(user_input: str) -> Dict[str, Any]:
    """Return {"intent": ..., "confidence": ..., "entities": {...}}."""

    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.0,
    )

    response = llm.invoke(
        [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]
    )

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from the response
        text = response.content
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(text[start:end])
        else:
            result = {
                "intent": "general_info",
                "confidence": 0.3,
                "entities": {},
            }

    return {
        "intent": result.get("intent", "general_info"),
        "confidence": float(result.get("confidence", 0.5)),
        "entities": result.get("entities", {}),
    }
