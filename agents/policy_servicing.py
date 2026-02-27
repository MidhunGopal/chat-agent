"""Policy Servicing Agent – handles policy queries.

Routes to: ApplicationSystem (policies table in DataHub)
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

import config
from data.hub import get_data_hub
from vectorstore.store import get_vector_store


_SYSTEM_PROMPT = """You are the Policy Servicing Agent for an insurance company.
You help customers and advisors with:
- Checking policy details (coverage, premium, dates, beneficiaries)
- Policy changes, endorsements, cancellations
- Claims inquiries
- Renewal information
- Premium payment questions

IMPORTANT GUARDRAIL: You must ONLY answer questions related to insurance policies, claims, premiums, and related services. If the user asks about anything outside this scope, respond with:
"I'm sorry, I can only assist with insurance-related questions. Please ask me about your policies, applications, claims, or any of our insurance products and services."
Do NOT attempt to answer out-of-scope questions.

You have access to the following policy data (if any) and relevant knowledge base context.
Be professional, accurate, and helpful.

POLICY DATA:
{policy_data}

KNOWLEDGE CONTEXT:
{knowledge_context}
"""


def handle(user_input: str, entities: dict, user_id: str = "", user_role: str = "customer") -> str:
    """Process a policy-related query."""

    hub = get_data_hub()
    vs = get_vector_store("insurance_knowledge")

    # Look up policy data
    policy_data = "No policy data found."
    policy_id = entities.get("policy_id", "")
    holder_name = entities.get("name", entities.get("holder_name", ""))

    if policy_id:
        if user_id and user_role != "admin":
            record = hub.get_policy_for_user(policy_id, user_id, user_role)
        else:
            record = hub.get_policy(policy_id)
        if record:
            policy_data = str(record)
    elif holder_name:
        if user_id and user_role != "admin":
            records = hub.search_policies_for_user(holder_name, user_id, user_role)
        else:
            records = hub.search_policies(holder_name)
        if records:
            policy_data = "\n".join(str(r) for r in records)
    elif user_id:
        # No specific entity extracted – fetch all policies for the logged-in user
        records = hub.get_policies_for_user(user_id, user_role)
        if records:
            policy_data = "\n".join(str(r) for r in records)

    # Vector search
    knowledge_context = ""
    docs = vs.query(user_input, n_results=3) if vs.count() > 0 else []
    knowledge_context = "\n---\n".join(d["document"] for d in docs)

    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.3,
    )

    # Build user context note for the LLM
    user_context = ""
    if user_id:
        user_context = f"\n\nUSER CONTEXT: The logged-in user has ID '{user_id}' and role '{user_role}'. The policy data above is filtered to only show records this user is authorised to access."

    response = llm.invoke(
        [
            SystemMessage(
                content=_SYSTEM_PROMPT.format(
                    policy_data=policy_data,
                    knowledge_context=knowledge_context or "None available.",
                ) + user_context
            ),
            HumanMessage(content=user_input),
        ]
    )

    return response.content
