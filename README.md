# TradeMind AI: Intelligent Trade Agent 📦🧠

TradeMind AI is an advanced, AI-powered agentic system designed to assist with international trade queries, tariff research, import/export rules, and trade policy documentation. 

The system leverages **LangGraph** to coordinate a multi-tool agent that dynamically routes queries between structured databases (using SQL) and unstructured documents (using PGVector and RAG) to provide comprehensive trade intelligence.

---

## 🏗️ Architecture Overview

The system operates as a hybrid agent that dynamically leverages two tools based on the user's query:
1. **SQL Database Agent:** Queries structured relational tables containing detailed HS Codes, tariffs, and rate lists (e.g. RoDTEP).
2. **Retrieval-Augmented Generation (RAG) Agent:** Performs semantic search across unstructured PDF policy manuals, utilizing a **CrossEncoder** model for semantic reranking of retrieved contexts to provide highly accurate citations.

Both tools are orchestrated by a **LangGraph state machine** that manages context memory and conversational state. The interface is served via a responsive **Streamlit** dashboard.

```mermaid
graph TD
    User([User Query]) --> UI[Streamlit Frontend]
    UI --> Agent[Intelligent Trade Agent - LangGraph]
    Agent --> Router{Route Query}
    Router -- Structured Data --> SQLTool[SQL Database Tool]
    Router -- Policy Text --> RAGTool[RAG Search & Reranker Tool]
    SQLTool --> PostgreSQL[(PostgreSQL DB)]
    RAGTool --> PGVector[(PGVector Database)]
    PGVector --> CrossEncoder[CrossEncoder Reranker]
    CrossEncoder --> LLM[Gemini LLM]
    PostgreSQL --> LLM
    LLM --> UI
```

---

## 📂 Directory Structure

The project files have been structured and categorized logically:

```directory
TradeMind AI/
│
├── src/                                  # Core application source code
│   ├── app.py                            # Streamlit chat interface and event-loop runner
│   └── intelligent_trade_agent.py        # Core LangGraph agent and tool orchestration
│
├── notebooks/                            # Jupyter Notebooks for setup, ETL, and prototypes
│   │
│   ├── ingestion/                        # PDF Ingestion, chunking, and database setup
│   │   ├── Gemini_VectorDB_Setup.ipynb   # Basic vector ingestion using Google GenAI SDK
│   │   ├── VectorDB_Setup (1).ipynb      # Layout-aware PDF chunking & loading
│   │   └── Vector_Import_policies.ipynb  # ETL pipeline for parsing import/export tables & policies
│   │
│   ├── agents/                           # Core Agent implementations
│   │   ├── Agentic_RAG_for_FTP.ipynb     # Agent with RAG and CrossEncoder reranking
│   │   └── Master_agent.ipynb            # The combined SQL + RAG LangGraph master agent
│   │
│   └── prototypes/                       # Early-stage prototypes and concept notebooks
│       ├── Langgraph_Agent.ipynb         # Simple LangGraph chatbot prototype
│       ├── SQL_Agent.ipynb               # Text-to-SQL database agent prototype
│       └── Streamlit_master_agent.ipynb  # Interactive workspace used to generate python sources
│
├── requirements.txt                      # Python dependencies list
└── .gitignore                            # Standard git ignore definitions
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python:** 3.10 or higher.
- **Database:** PostgreSQL instance with the `vector` (PGVector) extension installed. (The agent is pre-configured to connect to Supabase PostgreSQL, but can be customized).
- **API Keys:** A Gemini API key from Google AI Studio.

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone <your-repository-url>
cd "TradeMind AI"
pip install -r requirements.txt
```

### 3. Database & ETL Ingestion
If you are setting up the database from scratch:
1. Initialize the PostgreSQL schema and vector database by running the notebooks in `notebooks/ingestion/`.
2. Place your trade policy PDFs (e.g. Foreign Trade Policy chapters) inside the designated directories.
3. Run [Vector_Import_policies.ipynb](notebooks/ingestion/Vector_Import_policies.ipynb) to extract JSON representations of chapters, parse HS-code tables using layout analysis, and upload documents with their embeddings to PGVector.

### 4. Running the Web App
Run the Streamlit application from the root directory:
```bash
streamlit run src/app.py
```
This will launch a web dashboard in your browser (typically at `http://localhost:8501`) where you can interactively chat with the Intelligent Trade Agent.

---

## ⚙️ Configuration & Environment Variables

While connection details are hardcoded in the scripts for development, it is highly recommended to configure them using a `.env` file in the root directory:

```env
# API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=postgres
```

---

## 🛠️ Tech Stack
- **LLM Engine:** Google Gemini (via `ChatGoogleGenerativeAI`)
- **Agent Orchestrator:** LangGraph
- **Database / Vector Store:** PostgreSQL with PGVector extension (accessed via SQLAlchemy and LangChain PGVector integration)
- **Reranker:** CrossEncoder (`sentence-transformers/ms-marco-MiniLM-L-6-v2`)
- **Frontend Dashboard:** Streamlit
- **PDF Extraction:** PyMuPDF, UnstructuredLoader
