"""Application Servicing Agent – handles new application queries.

Routes to: UnderwritingSystem (applications table in DataHub)
Also connects to: Proactive Notification (simulated).
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

import config
from data.hub import get_data_hub
from vectorstore.store import get_vector_store


_SYSTEM_PROMPT = """You are the Application Servicing Agent for an insurance company.
You help customers and advisors with:
- Checking application status
- Starting new insurance applications
- Updating existing applications
- Answering questions about the application process

IMPORTANT GUARDRAIL: You must ONLY answer questions related to insurance applications and related services. If the user asks about anything outside this scope, respond with:
"I'm sorry, I can only assist with insurance-related questions. Please ask me about your policies, applications, claims, or any of our insurance products and services."
Do NOT attempt to answer out-of-scope questions.

You have access to the following application data (if any) and relevant knowledge base context.
Be professional, helpful, and concise. If you cannot find the requested data,
let the customer know and suggest next steps.

APPLICATION DATA:
{app_data}

KNOWLEDGE CONTEXT:
{knowledge_context}
"""


def handle(user_input: str, entities: dict, user_id: str = "", user_role: str = "customer") -> str:
    """Process an application-related query."""

    hub = get_data_hub()
    vs = get_vector_store("insurance_knowledge")

    # Try to look up application data
    app_data = "No application data found."
    app_id = entities.get("application_id", "")
    applicant_name = entities.get("name", entities.get("applicant_name", ""))

    if app_id:
        if user_id and user_role != "admin":
            record = hub.get_application_for_user(app_id, user_id, user_role)
        else:
            record = hub.get_application(app_id)
        if record:
            app_data = str(record)
    elif applicant_name:
        if user_id and user_role != "admin":
            records = hub.search_applications_for_user(applicant_name, user_id, user_role)
        else:
            records = hub.search_applications(applicant_name)
        if records:
            app_data = "\n".join(str(r) for r in records)
    elif user_id:
        # No specific entity extracted – fetch all applications for the logged-in user
        records = hub.get_applications_for_user(user_id, user_role)
        if records:
            app_data = "\n".join(str(r) for r in records)

    # Vector search for relevant knowledge
    knowledge_context = ""
    docs = vs.query(user_input, n_results=3, where={"category": "application"}) if vs.count() > 0 else []
    if not docs:
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
        user_context = f"\n\nUSER CONTEXT: The logged-in user has ID '{user_id}' and role '{user_role}'. The application data above is filtered to only show records this user is authorised to access."

    response = llm.invoke(
        [
            SystemMessage(
                content=_SYSTEM_PROMPT.format(
                    app_data=app_data, knowledge_context=knowledge_context or "None available."
                ) + user_context
            ),
            HumanMessage(content=user_input),
        ]
    )

    return response.content
