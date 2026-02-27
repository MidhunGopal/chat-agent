# 🏢 AI Customer & Advisor Assistant — Agentic Ecosystem

A multi-agent insurance customer service system built with **LangGraph**, **FAISS**, **OpenAI**, and **Streamlit**.

## 🏗️ Architecture

```
📡 Input Channels
┌──────────────┬───────────────┬──────────────┬─────────────┬────────────────┐
│   Website    │  My Accounts  │  Agent Hub   │   Email     │   Letters      │
└──────┬───────┴───────┬───────┴──────┬───────┴──────┬──────┴───────┬────────┘
       └───────────────┴──────────────┴──────────────┴──────────────┘
                                      │
                    ┌─────────────────┴──────────────────┐
                    │  Customer/Agent Intent Routing Agent │
                    └─────────┬───────────────────────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
  ┌─────┴──────┐   ┌────────┴────────┐   ┌─────────┴──────┐
  │ Application│   │  Underwriting   │   │    Policy      │
  │ Servicing  │   │   Support       │   │   Servicing    │
  │   Agent    │   │   Agent         │   │    Agent       │
  └─────┬──────┘   └────────┬────────┘   └─────────┬──────┘
        │                   │                       │
  ┌─────┴──────┐   ┌───────┴────────┐   ┌─────────┴──────┐
  │ Proactive  │   │   Document     │   │    Policy      │
  │Notification│   │ Intelligence   │   │  Information   │
  │   Agent    │   │    Agent       │   │    Agent       │
  └────────────┘   └───────┬────────┘   └────────────────┘
                           │
              ┌────────────┴────────────┐
              │   Data Hub              │
              │   (Event Stream + Cache)│
              └─────┬──────┬──────┬─────┘
                    │      │      │
              ┌─────┴┐  ┌──┴──┐  ┌┴──────────┐
              │ ApplicationSystem │  │ UnderwritingSystem │  │ PolicyAdminSystem │  │ CommunicationSystem │
              └──────┘  └─────┘  └───────────┘  └────────────┘
```

## 🛠️ Tech Stack

| Component       | Technology                          |
|----------------|-------------------------------------|
| Orchestration  | LangGraph (stateful workflow graph)  |
| LLM            | OpenAI GPT-4o-mini                  |
| Vector DB       | FAISS (persistent, cosine similarity)|
| Embeddings     | OpenAI text-embedding-3-small       |
| Chunking       | LangChain RecursiveCharacterTextSplitter |
| Database       | SQLite (persistent)                 |
| UI             | Streamlit                           |

## 🚀 Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Edit the `.env` file and set your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Seed the databases

```bash
python seed_data.py
```

This populates:
- **SQLite**: Sample policies, applications, underwriting records
- **FAISS**: Knowledge base articles (chunked & embedded)

### 4. Run the application

```bash
streamlit run app.py
```

## 📁 Project Structure

```
chat-agent/
├── app.py                          # Streamlit main application
├── config.py                       # Configuration & environment
├── seed_data.py                    # Database seeding script
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables
│
├── agents/                         # Specialized AI agents
│   ├── intent_router.py            # NLP intent classification
│   ├── application_servicing.py    # New application handling
│   ├── underwriting_support.py     # Underwriting status & info
│   ├── policy_servicing.py         # Existing policy queries
│   ├── policy_information.py       # General insurance info (RAG)
│   ├── document_intelligence.py    # Document processing
│   └── sentiment_analyzer.py       # Response quality analysis
│
├── graph/                          # LangGraph workflow
│   └── workflow.py                 # Full agentic workflow graph
│
├── vectorstore/                    # FAISS vector store
│   ├── chunker.py                  # Document chunking
│   └── store.py                    # Vector store operations
│
├── data/                           # Persistent data layer
│   └── hub.py                      # SQLite DataHub (ApplicationSystem/UnderwritingSystem/PolicyAdminSystem/CommunicationSystem)
│
├── models/                         # Pydantic schemas
│   └── schemas.py                  # Data models & enums
│
└── utils/                          # Utilities
    └── helpers.py                  # Helper functions
```

## 🔄 Workflow

1. **Capture Input** — User query arrives via any input channel
2. **Intent Classification** — OpenAI classifies into 5 categories
3. **Agent Routing** — LangGraph routes to the specialized agent
4. **Agent Processing** — Agent queries DataHub + FAISS for context
5. **Sentiment Analysis** — Response quality is evaluated
6. **Delivery Decision**:
   - ✅ **High satisfaction** → Deliver to user
   - 🔄 **Low satisfaction** → Refine and re-evaluate
   - 🚨 **Complex/Unknown** → Escalate to human agent
7. **Logging** — All interactions are logged for learning

## 💡 Sample Queries

- "What is the status of application APP-001?"
- "Tell me about policy POL-001 for John Smith"
- "What types of life insurance do you offer?"
- "What is the underwriting status for David Lee's application?"
- "I need to upload documents for my disability insurance application"
