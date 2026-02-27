"""Document Intelligence Agent – handles document upload and processing.

Chunks uploaded documents, stores in ChromaDB, and provides analysis.
Routes to: CommunicationSystem (documents table in DataHub).
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

import config
from data.hub import get_data_hub
from vectorstore.store import get_vector_store
from vectorstore.chunker import chunk_text
from utils.helpers import new_id, now_iso


_SYSTEM_PROMPT = """You are the Document Intelligence Agent for an insurance company.
You help with:
- Processing uploaded documents (IDs, medical reports, financial statements, etc.)
- Extracting key information from documents
- Classifying document types
- Confirming document receipt and status

IMPORTANT GUARDRAIL: You must ONLY answer questions related to insurance documents and related services. If the user asks about anything outside this scope, respond with:
"I'm sorry, I can only assist with insurance-related questions. Please ask me about your policies, applications, claims, or any of our insurance products and services."
Do NOT attempt to answer out-of-scope questions.

Given the document content below (if any), analyze it and provide a summary
of the key information extracted.

DOCUMENT CONTENT (excerpt):
{doc_content}

RELATED CONTEXT:
{related_context}
"""


def handle(user_input: str, entities: dict, document_text: str | None = None) -> str:
    """Process a document-related query or uploaded document."""

    hub = get_data_hub()
    vs = get_vector_store("insurance_documents")

    doc_content = "No document uploaded."
    related_context = ""

    if document_text:
        # Store document in DataHub
        doc_id = new_id("doc")
        hub.store_document(
            {
                "document_id": doc_id,
                "reference_id": entities.get("policy_id", entities.get("application_id", "")),
                "doc_type": entities.get("doc_type", "general"),
                "content": document_text[:5000],  # Store first 5000 chars
                "metadata": {"source": "upload", "entities": str(entities)},
                "created_at": now_iso(),
            }
        )

        # Chunk and store in vector DB
        vs.add_document(
            text=document_text,
            metadata={
                "document_id": doc_id,
                "doc_type": entities.get("doc_type", "general"),
                "category": "uploaded_document",
            },
            doc_id_prefix=doc_id,
        )

        doc_content = document_text[:3000]

    # Search for related documents
    docs = vs.query(user_input, n_results=3) if vs.count() > 0 else []
    related_context = "\n---\n".join(d["document"] for d in docs)

    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.3,
    )

    response = llm.invoke(
        [
            SystemMessage(
                content=_SYSTEM_PROMPT.format(
                    doc_content=doc_content,
                    related_context=related_context or "None available.",
                )
            ),
            HumanMessage(content=user_input),
        ]
    )

    return response.content
