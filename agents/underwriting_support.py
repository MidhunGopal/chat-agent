"""Underwriting Support Agent – handles underwriting status queries.

Routes to: PolicyAdminSystem (underwriting table in DataHub)
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

import config
from data.hub import get_data_hub
from vectorstore.store import get_vector_store


_SYSTEM_PROMPT = """You are the Underwriting Support Agent for an insurance company.
You help customers and advisors with:
- Checking underwriting status for applications
- Explaining underwriting decisions
- Providing risk assessment information
- Answering questions about the underwriting process and timelines

IMPORTANT: Always display all currency and monetary values in British Pounds Sterling (£ / GBP). Never use dollars ($) or any other currency symbol.

IMPORTANT GUARDRAIL: You must ONLY answer questions related to underwriting, risk assessment, and insurance applications. If the user asks about anything outside this scope, respond with:
"I'm sorry, I can only assist with insurance-related questions. Please ask me about your policies, applications, claims, or any of our insurance products and services."
Do NOT attempt to answer out-of-scope questions.

You have access to the following underwriting data (if any) and relevant knowledge base context.
Be professional, clear, and empathetic. 

UNDERWRITING DATA:
{uw_data}

APPLICATION DATA:
{app_data}

KNOWLEDGE CONTEXT:
{knowledge_context}
"""


def handle(user_input: str, entities: dict, user_id: str = "", user_role: str = "customer") -> str:
    """Process an underwriting-related query."""

    hub = get_data_hub()
    vs = get_vector_store("insurance_knowledge")

    # Try to look up underwriting data
    uw_data = "No underwriting data found."
    app_data = "No application data found."
    app_id = entities.get("application_id", "")
    applicant_name = entities.get("name", entities.get("applicant_name", ""))

    if app_id:
        uw_record = hub.get_underwriting(app_id)
        if uw_record:
            uw_data = str(uw_record)
        if user_id and user_role != "admin":
            app_record = hub.get_application_for_user(app_id, user_id, user_role)
        else:
            app_record = hub.get_application(app_id)
        if app_record:
            app_data = str(app_record)
    elif applicant_name:
        if user_id and user_role != "admin":
            apps = hub.search_applications_for_user(applicant_name, user_id, user_role)
        else:
            apps = hub.search_applications(applicant_name)
        if apps:
            app_data = "\n".join(str(a) for a in apps)
            for app in apps:
                uw = hub.get_underwriting(app["application_id"])
                if uw:
                    uw_data = str(uw)
                    break
    elif user_id:
        # No specific entity extracted – fetch all applications for the logged-in user
        apps = hub.get_applications_for_user(user_id, user_role)
        if apps:
            app_data = "\n".join(str(a) for a in apps)
            uw_parts = []
            for app in apps:
                uw = hub.get_underwriting(app["application_id"])
                if uw:
                    uw_parts.append(str(uw))
            if uw_parts:
                uw_data = "\n".join(uw_parts)

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
        user_context = f"\n\nUSER CONTEXT: The logged-in user has ID '{user_id}' and role '{user_role}'. The data above is filtered to only show records this user is authorised to access."

    response = llm.invoke(
        [
            SystemMessage(
                content=_SYSTEM_PROMPT.format(
                    uw_data=uw_data,
                    app_data=app_data,
                    knowledge_context=knowledge_context or "None available.",
                ) + user_context
            ),
            HumanMessage(content=user_input),
        ]
    )

    return response.content
