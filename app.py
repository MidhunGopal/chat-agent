"""
Streamlit UI for the AI Customer & Advisor Assistant Ecosystem.

Supports three user roles:
  - Guest (Direct/Partner Website): Knowledge agent only, no login.
  - Customer (Self Servicing Portal): Chat with full agents, sees own data.
  - Agent (Agent Portal): Chat with full agents, sees assigned data.
  - Admin: Full access – dashboard, data explorer, architecture, all data.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import os
import sys
import json

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

from graph.workflow import run_query
from data.hub import get_data_hub
from vectorstore.store import get_vector_store
from seed_data import seed_all
from utils.helpers import new_id


# ── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Customer & Advisor Assistant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ────────────────────────────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = new_id("session")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "db_seeded" not in st.session_state:
    st.session_state.db_seeded = False
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "access_mode" not in st.session_state:
    # "login_screen" | "guest" | "authenticated"
    st.session_state.access_mode = "login_screen"


# ── Helper: derive channel from user role ────────────────────────────────────

def _channel_for_role(role: str) -> str:
    """Map user role to the appropriate input channel."""
    return {
        "customer": "my_accounts_portal",
        "agent": "agent_hub_portal",
        "admin": "my_accounts_portal",
    }.get(role, "direct_partner_website")


def _is_intent_allowed(intent: str, access_mode: str) -> bool:
    """
    Guest users can only access the knowledge agent (general_info).
    out_of_scope is always allowed (so the polite decline can be shown).
    Authenticated users can access all agents.
    """
    if intent == "out_of_scope":
        return True  # Let the out-of-scope handler respond with its polite decline
    if access_mode == "guest":
        return intent in ("general_info",)
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN / CHANNEL SELECTION SCREEN
# ══════════════════════════════════════════════════════════════════════════════

def show_login_screen():
    """Render the entry / login screen."""
    st.title("🏢 InsureCo AI – Welcome")
    st.markdown("Choose how you'd like to access the system.")

    col_left, col_right = st.columns([1, 1], gap="large")

    # ── Left: Direct / Guest access ─────────────────────────────────────
    with col_left:
        st.subheader("🌐 Direct / Partner Website")
        st.markdown(
            "Access our **Knowledge Assistant** without logging in.  \n"
            "You can ask general questions about insurance products, processes, and more."
        )
        if st.button("Continue as Guest", use_container_width=True, key="guest_btn"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.access_mode = "guest"
            st.session_state.messages = []
            st.rerun()

    # ── Right: Login ─────────────────────────────────────────────────────
    with col_right:
        st.subheader("🔐 Login")
        st.markdown("Log in as **Customer**, **Agent**, or **Admin** to access full features.")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password.")
            else:
                hub = get_data_hub()
                user = hub.authenticate_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.access_mode = "authenticated"
                    st.session_state.messages = []
                    st.session_state.session_id = new_id("session")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")

        # Hint table
        st.markdown("---")
        st.caption("**Demo Credentials** (after seeding):")
        st.markdown(
            "| Role | Username | Password |\n"
            "|------|----------|----------|\n"
            "| Customer | `john.smith` | `password123` |\n"
            "| Customer | `david.lee` | `password123` |\n"
            "| Agent | `agent.wilson` | `agent123` |\n"
            "| Agent | `agent.martinez` | `agent123` |\n"
            "| Admin | `admin` | `admin123` |"
        )

    # ── Bottom: Seed button (always available) ───────────────────────────
    st.markdown("---")
    if st.button("🌱 Seed Sample Data (first-time setup)", use_container_width=True, key="seed_login"):
        with st.spinner("Seeding databases..."):
            seed_all()
            st.session_state.db_seeded = True
        st.success("Databases seeded successfully! You can now log in with the demo credentials above.")


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTING: Login screen vs main app
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.access_mode == "login_screen":
    show_login_screen()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION (post-login or guest)
# ══════════════════════════════════════════════════════════════════════════════

user = st.session_state.user  # None for guest
user_role = user["role"] if user else None
user_id = user["user_id"] if user else ""
channel = _channel_for_role(user_role) if user_role else "direct_partner_website"
is_guest = st.session_state.access_mode == "guest"
is_admin = user_role == "admin"
uploaded_text = None


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/insurance.png",
        width=64,
    )
    st.title("🏢 InsureCo AI")

    # Show user info
    if user:
        role_emoji = {"customer": "👤", "agent": "🏷️", "admin": "🛡️"}.get(user_role, "👤")
        st.markdown(f"**{role_emoji} {user['full_name']}**")
        st.caption(f"Role: **{user_role.capitalize()}**")
    else:
        st.markdown("**🌐 Guest Access**")
        st.caption("Knowledge Assistant only")

    st.markdown("---")

    # ── Admin-only: System Management ────────────────────────────────────
    if is_admin:
        st.subheader("⚙️ System Management")

        if st.button("🌱 Seed Sample Data", use_container_width=True, key="seed_main"):
            with st.spinner("Seeding databases..."):
                seed_all()
                st.session_state.db_seeded = True
            st.success("Databases seeded successfully!")

        # Show DB stats
        try:
            hub = get_data_hub()
            vs = get_vector_store("insurance_knowledge")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📄 Vectors", vs.count())
            with col2:
                st.metric("💾 Policies", len(hub.get_all_policies()))
        except Exception:
            st.info("Click 'Seed Sample Data' to initialize.")

        st.markdown("---")

    # ── Document Upload (customers and admins only) ──────────────────────
    if not is_guest and user_role in ("customer", "admin"):
        st.subheader("📎 Document Upload")
        uploaded_file = st.file_uploader(
            "Upload a document for processing",
            type=["txt", "pdf", "docx"],
            help="Upload documents for the Document Intelligence Agent",
        )
        if uploaded_file:
            if uploaded_file.type == "text/plain":
                uploaded_text = uploaded_file.read().decode("utf-8")
            else:
                uploaded_text = (
                    f"[Uploaded file: {uploaded_file.name}, "
                    f"type: {uploaded_file.type}, size: {uploaded_file.size} bytes]"
                )
            st.success(f"📎 {uploaded_file.name} ready for processing")

        st.markdown("---")

    # Session info & logout
    st.caption(f"Session: `{st.session_state.session_id[:20]}...`")
    if st.button("🔄 New Session", use_container_width=True, key="new_session"):
        st.session_state.session_id = new_id("session")
        st.session_state.messages = []
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True, key="logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.access_mode = "login_screen"
        st.session_state.messages = []
        st.session_state.session_id = new_id("session")
        st.rerun()


# ── Main Content ─────────────────────────────────────────────────────────────

if is_guest:
    st.title("🤖 Insurance Knowledge Assistant")
    st.markdown(
        "Welcome! Ask me anything about insurance products, processes, and general information.  \n"
        "**Log in** to access your policies, applications, and full self-service features."
    )
else:
    st.title("🤖 AI Customer & Advisor Assistant")
    st.markdown(
        f"Welcome back, **{user['full_name']}**! I can help you with insurance applications, "
        "policy queries, underwriting status, general information, and document processing."
    )

# ── Build tabs based on role ─────────────────────────────────────────────────

if is_admin:
    tab_chat, tab_dashboard, tab_data, tab_architecture = st.tabs(
        ["💬 Chat", "📊 Dashboard", "🗄️ Data Explorer", "🏗️ Architecture"]
    )
else:
    # Guest, Customer, Agent → chat only
    tab_chat = st.tabs(["💬 Chat"])[0]


# ── Chat Tab ─────────────────────────────────────────────────────────────────

with tab_chat:
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("metadata"):
                meta = msg["metadata"]
                cols = st.columns(4)
                with cols[0]:
                    st.caption(f"🎯 Intent: **{meta.get('intent', 'N/A')}**")
                with cols[1]:
                    st.caption(f"🤖 Agent: **{meta.get('agent', 'N/A')}**")
                with cols[2]:
                    score = meta.get("sentiment", 0)
                    emoji = "🟢" if score > 0.7 else "🟡" if score > 0.4 else "🔴"
                    st.caption(f"{emoji} Sentiment: **{score:.2f}**")
                with cols[3]:
                    if meta.get("escalated"):
                        st.caption("🚨 **ESCALATED**")
                    else:
                        st.caption("✅ **Delivered**")

    # Chat input
    placeholder = (
        "Ask about insurance products, processes, or general info..."
        if is_guest
        else "Ask about your insurance policy, application, or any question..."
    )
    if prompt := st.chat_input(placeholder):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process through workflow
        with st.chat_message("assistant"):
            with st.spinner("Processing your request through the AI agent network..."):
                try:
                    result = run_query(
                        user_input=prompt,
                        session_id=st.session_state.session_id,
                        input_channel=channel,
                        uploaded_document=uploaded_text if not is_guest else None,
                        user_id=user_id,
                        user_role=user_role or "guest",
                    )

                    detected_intent = result.get("intent", "general_info")

                    # Enforce access: guests can only use knowledge agent
                    if is_guest and not _is_intent_allowed(detected_intent, "guest"):
                        response = (
                            "I can only answer general insurance questions in guest mode. "
                            "Please **log in** to access your policies, applications, "
                            "and full self-service features."
                        )
                    else:
                        response = result.get(
                            "final_response",
                            "I'm sorry, I couldn't process your request.",
                        )

                    st.markdown(response)

                    # Show metadata
                    meta = {
                        "intent": result.get("intent", "N/A"),
                        "confidence": result.get("intent_confidence", 0),
                        "agent": result.get("routed_agent", "N/A"),
                        "sentiment": result.get("sentiment_score", 0),
                        "escalated": result.get("escalated", False),
                        "entities": result.get("entities", {}),
                    }

                    cols = st.columns(4)
                    with cols[0]:
                        st.caption(
                            f"🎯 Intent: **{meta['intent']}** ({meta['confidence']:.0%})"
                        )
                    with cols[1]:
                        st.caption(f"🤖 Agent: **{meta['agent']}**")
                    with cols[2]:
                        score = meta["sentiment"]
                        emoji = "🟢" if score > 0.7 else "🟡" if score > 0.4 else "🔴"
                        st.caption(f"{emoji} Sentiment: **{score:.2f}**")
                    with cols[3]:
                        if meta["escalated"]:
                            st.caption("🚨 **ESCALATED**")
                        else:
                            st.caption("✅ **Delivered**")

                    # Save to messages
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                            "metadata": meta,
                        }
                    )

                except Exception as e:
                    error_msg = f"❌ Error processing request: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

    # Quick action buttons
    st.markdown("---")
    st.markdown("**💡 Quick Actions:**")

    if is_guest:
        col1, col2 = st.columns(2)
        quick_queries = {
            "❓ Insurance Types": "What types of life insurance do you offer?",
            "📖 Claims Process": "How do I file an insurance claim?",
        }
        for col, (label, query) in zip([col1, col2], quick_queries.items()):
            with col:
                if st.button(label, use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": query})
                    st.rerun()
    else:
        col1, col2, col3, col4, col5 = st.columns(5)
        quick_queries = {
            "📋 Application Status": "What is the status of my application?",
            "📊 Underwriting": "What is my underwriting status?",
            "📑 Policy Info": "Show me my policy details",
            "❓ General FAQ": "What types of life insurance do you offer?",
            "📎 Upload Help": "I need to upload documents for my insurance application",
        }
        for col, (label, query) in zip(
            [col1, col2, col3, col4, col5], quick_queries.items()
        ):
            with col:
                if st.button(label, use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": query})
                    st.rerun()


# ── Dashboard Tab (Admin only) ───────────────────────────────────────────────

if is_admin:
    with tab_dashboard:
        st.subheader("📊 Interaction Dashboard")

        try:
            hub = get_data_hub()
            interactions = hub.get_recent_interactions(limit=100)

            if interactions:
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Interactions", len(interactions))
                with col2:
                    escalated = sum(1 for i in interactions if i.get("escalated"))
                    st.metric("Escalated", escalated)
                with col3:
                    avg_sentiment = (
                        sum(i.get("sentiment_score", 0) for i in interactions)
                        / len(interactions)
                    )
                    st.metric("Avg Sentiment", f"{avg_sentiment:.2f}")
                with col4:
                    intents = {}
                    for i in interactions:
                        intent = i.get("intent", "unknown")
                        intents[intent] = intents.get(intent, 0) + 1
                    top_intent = max(intents, key=intents.get) if intents else "N/A"
                    st.metric("Top Intent", top_intent)

                st.markdown("---")

                # Intent distribution
                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("🎯 Intent Distribution")
                    if intents:
                        import pandas as pd

                        df_intents = pd.DataFrame(
                            list(intents.items()), columns=["Intent", "Count"]
                        )
                        st.bar_chart(df_intents.set_index("Intent"))

                with col_right:
                    st.subheader("🤖 Agent Usage")
                    agents = {}
                    for i in interactions:
                        agent = i.get("agent_used", "unknown")
                        agents[agent] = agents.get(agent, 0) + 1
                    if agents:
                        import pandas as pd

                        df_agents = pd.DataFrame(
                            list(agents.items()), columns=["Agent", "Count"]
                        )
                        st.bar_chart(df_agents.set_index("Agent"))

                # Recent interactions table
                st.markdown("---")
                st.subheader("📝 Recent Interactions")
                import pandas as pd

                df = pd.DataFrame(interactions)
                display_cols = [
                    c
                    for c in [
                        "timestamp",
                        "intent",
                        "agent_used",
                        "sentiment_score",
                        "escalated",
                        "user_query",
                    ]
                    if c in df.columns
                ]
                if display_cols:
                    st.dataframe(df[display_cols].head(20), use_container_width=True)
            else:
                st.info("No interactions yet. Start chatting to generate data!")

        except Exception as e:
            st.warning(f"Dashboard data not available: {e}")
            st.info(
                "Click 'Seed Sample Data' in the sidebar to initialize the databases."
            )


# ── Data Explorer Tab (Admin only) ───────────────────────────────────────────

if is_admin:
    with tab_data:
        st.subheader("🗄️ Data Explorer")

        try:
            hub = get_data_hub()

            data_tab1, data_tab2, data_tab3, data_tab4, data_tab5 = st.tabs(
                [
                    "📋 Policies (POLICYADMINSYSTEM)",
                    "📝 Applications (APPLICATIONSYSTEM)",
                    "🔍 Underwriting (UNDERWRITINGSYSTEM)",
                    "📄 Knowledge Base",
                    "👥 Users",
                ]
            )

            with data_tab1:
                policies = hub.get_all_policies()
                if policies:
                    import pandas as pd

                    st.dataframe(pd.DataFrame(policies), use_container_width=True)
                else:
                    st.info("No policies found. Seed the database first.")

            with data_tab2:
                applications = hub.get_all_applications()
                if applications:
                    import pandas as pd

                    st.dataframe(pd.DataFrame(applications), use_container_width=True)
                else:
                    st.info("No applications found. Seed the database first.")

            with data_tab3:
                st.markdown("Search underwriting by Application ID:")
                app_id = st.text_input("Application ID", value="APP-001")
                if st.button("Search Underwriting"):
                    uw = hub.get_underwriting(app_id)
                    if uw:
                        st.json(uw)
                    else:
                        st.warning(f"No underwriting record found for {app_id}")

            with data_tab4:
                st.markdown("Search knowledge base:")
                keyword = st.text_input("Search keyword", value="insurance")
                if st.button("Search Knowledge Base"):
                    articles = hub.search_knowledge(keyword)
                    if articles:
                        for a in articles:
                            with st.expander(
                                f"📖 {a.get('title', 'Untitled')} ({a.get('category', '')})"
                            ):
                                st.markdown(a.get("content", ""))
                    else:
                        st.warning("No articles found.")

                # Vector store stats
                st.markdown("---")
                vs = get_vector_store("insurance_knowledge")
                st.metric("FAISS Vector Count", vs.count())

                if vs.count() > 0:
                    search_query = st.text_input(
                        "🔍 Semantic Search (Vector DB)",
                        value="life insurance coverage",
                    )
                    if st.button("Search Vectors"):
                        results = vs.query(search_query, n_results=5)
                        for r in results:
                            with st.expander(
                                f"📎 {r['id']} (distance: {r['distance']:.4f})"
                            ):
                                st.markdown(r["document"])
                                st.caption(
                                    f"Metadata: {json.dumps(r['metadata'], indent=2)}"
                                )

            with data_tab5:
                users = hub.get_all_users()
                if users:
                    import pandas as pd

                    st.dataframe(pd.DataFrame(users), use_container_width=True)
                else:
                    st.info("No users found. Seed the database first.")

        except Exception as e:
            st.warning(f"Data explorer not available: {e}")
            st.info(
                "Click 'Seed Sample Data' in the sidebar to initialize the databases."
            )


# ── Architecture Tab (Admin only) ────────────────────────────────────────────

if is_admin:
    with tab_architecture:
        st.subheader("🏗️ System Architecture")

        st.markdown(
            """
### AI Customer & Advisor Assistants - Agentic Ecosystem

This system implements a multi-agent architecture for insurance customer service,
built with **LangGraph**, **FAISS**, **OpenAI**, and **Streamlit**.

---

#### 👥 User Roles & Access
| Role | Access | Login Required |
|------|--------|---------------|
| **Guest** | Knowledge Agent (general FAQ) only | No |
| **Customer** | Chat – policies, applications, underwriting (own data) | Yes |
| **Agent** | Chat – policies, applications, underwriting (assigned data) | Yes |
| **Admin** | Full access – all data, dashboard, data explorer, architecture | Yes |

---

#### 📡 Input Channels
| Channel | Description |
|---------|-------------|
| 🌐 Direct/Partner Website | Guest access – knowledge only |
| 👤 Self Servicing Portal | Customer self-service |
| 🏷️ Agent Portal | Insurance advisor interface |
| 📧 Email Inbound | Email processing pipeline |
| ✉️ Letters Inbound | Physical mail digitization |

---

#### 🤖 Agent Network

```
Customer/Agent Interaction
        ↓
  Capture Input (Query/Email/Letter)
        ↓
  NLP Processing & Intent Classification
        ↓
  ◇ Intent Router ──────────────────────────────────
  │                                                  │
  ├─ New Application  → Application Servicing Agent  │
  ├─ Underwriting     → Underwriting Support Agent   │
  ├─ Policy Query     → Policy Servicing Agent       │
  ├─ General Info     → Policy Information Agent     │
  └─ Document Upload  → Document Intelligence Agent  │
  ────────────────────────────────────────────────────
        ↓
  Sentiment Analysis
        ↓
  ◇ Satisfaction Predicted?
  │  HIGH    → ✅ Deliver Response → Log & Learn → END
  │  LOW     → 🔄 Refine Response → Re-analyze
  │  UNKNOWN → 🚨 Escalate to Human Agent → Handoff
```

---

#### 💾 Data Layer
| System | Purpose | Technology |
|--------|---------|------------|
| **POLICYADMINSYSTEM** | Policy management | SQLite (policies table) |
| **APPLICATIONSYSTEM** | Applications | SQLite (applications table) |
| **UNDERWRITINGSYSTEM** | Underwriting | SQLite (underwriting table) |
| **COMMUNICATIONSYSTEM** | Documents & correspondence | SQLite + FAISS |
| **Knowledge Base** | RAG knowledge articles | FAISS (vector store) |

---

#### 🛠️ Technology Stack
- **Orchestration**: LangGraph (stateful workflow graph)
- **LLM**: OpenAI GPT-4o-mini (via LangChain)
- **Vector DB**: FAISS (persistent, cosine similarity)
- **Embeddings**: OpenAI text-embedding-3-small
- **Chunking**: RecursiveCharacterTextSplitter
- **Database**: SQLite (persistent)
- **UI**: Streamlit
"""
        )

        # Show the graph visualization
        st.markdown("---")
        st.subheader("📐 Workflow Graph")
        try:
            from graph.workflow import get_workflow

            wf = get_workflow()
            graph_png = wf.get_graph().draw_mermaid()
            st.code(graph_png, language="mermaid")
        except Exception as e:
            st.info(f"Graph visualization: {e}")
            st.markdown(
                "Install `pygraphviz` or view the Mermaid diagram above for the workflow graph."
            )
