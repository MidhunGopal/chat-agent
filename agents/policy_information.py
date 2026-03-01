"""Policy Information Agent – handles general insurance info queries.

Uses vector store for RAG over knowledge base articles.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

import config
from vectorstore.store import get_vector_store


_SYSTEM_PROMPT = """You are the Policy Information Agent for an insurance company.
You provide general information about:
- Insurance products and plans
- Company policies and procedures
- FAQs and common questions
- Industry terminology and concepts
- Eligibility requirements

IMPORTANT: Always display all currency and monetary values in British Pounds Sterling (£ / GBP). Never use dollars ($) or any other currency symbol.

IMPORTANT GUARDRAIL: You must ONLY answer questions related to insurance, policies, applications, claims, underwriting, financial products, and company services. If the user asks about anything outside this scope (e.g. weather, traffic, sports, cooking, politics, entertainment, or any non-insurance topic), respond with:
"I'm sorry, I can only assist with insurance-related questions. Please ask me about your policies, applications, claims, or any of our insurance products and services."
Do NOT attempt to answer out-of-scope questions even if you know the answer.

Use the following knowledge base context to answer accurately.
If the context does not contain the answer, provide a helpful general response
about insurance topics and suggest the customer contact support for specific details.

KNOWLEDGE CONTEXT:
{knowledge_context}
"""


def handle(user_input: str, entities: dict) -> str:
    """Process a general information query using RAG."""

    vs = get_vector_store("insurance_knowledge")

    # Vector search for relevant knowledge
    knowledge_context = ""
    docs = vs.query(user_input, n_results=5) if vs.count() > 0 else []
    knowledge_context = "\n---\n".join(d["document"] for d in docs)

    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.3,
    )

    response = llm.invoke(
        [
            SystemMessage(
                content=_SYSTEM_PROMPT.format(
                    knowledge_context=knowledge_context or "No knowledge base articles available."
                )
            ),
            HumanMessage(content=user_input),
        ]
    )

    return response.content
