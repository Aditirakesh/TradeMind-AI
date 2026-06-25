# 🧠 TradeMind AI

An intelligent chatbot for Indian international trade — powered by Gemini AI, LangGraph, and PostgreSQL (Supabase).

**Author:** Aditi

## Features

- 🤖 **AI-Powered Trade Assistant** — Ask about HS codes, import/export policies, FTP schemes
- 📊 **SQL + RAG Hybrid** — Combines structured database queries with semantic document retrieval
- 🔍 **Smart Re-Ranking** — Uses cross-encoder models for precise document matching
- 🗄️ **Supabase PostgreSQL** — Vector store + relational data in one database

## Project Structure

```
TradeMind AI/
├── config.py                  # Centralized credentials & settings
├── requirements.txt           # Python dependencies
├── requirements_pinned.txt    # Pinned dependency versions
├── run.py                     # One-click launcher
├── README.md                  # This file
│
├── agents/                    # AI Agent modules
│   ├── __init__.py
│   └── intelligent_trade_agent.py   # Main trade agent (SQL + RAG + Re-ranking)
│
├── app/                       # Streamlit web application
│   └── app.py                 # Chat interface
│
├── data_ingestion/            # Data loading package
│   └── __init__.py
│
└── notebooks/                 # Original Jupyter notebooks (reference & setup)
    ├── Agentic_RAG_for_FTP.ipynb
    ├── Gemini_VectorDB_Setup.ipynb
    ├── Langgraph_Agent.ipynb
    ├── Master_agent.ipynb
    ├── SQL_Agent.ipynb
    ├── Streamlit_master_agent.ipynb
    ├── VectorDB_Setup (1).ipynb
    └── Vector_Import_policies.ipynb
```

## Quick Start

### 1. Install Dependencies
Ensure you are in the project root and activate your virtual environment:
```bash
pip install -r requirements.txt
```

### 2. Run the App
To run the Streamlit app on Windows:

*   **Option 1: Direct execution (Recommended)**
    ```powershell
    .venv\Scripts\python.exe run.py
    ```
*   **Option 2: Activate virtual environment first**
    ```powershell
    .venv\Scripts\Activate.ps1
    python run.py
    ```

The app will start at **http://localhost:8501** (or automatically prompt the next available port if 8501 is taken).

### 3. Ask Questions!
Try queries like:
- *"I want to import green peas"*
- *"What is the RoDTEP scheme?"*
- *"How does milk export works?"*
- *"What are the EPCG scheme rules?"*

## Configuration

All settings are in [config.py](file:///d:/WorkSpace/TradeMind AI/config.py):
- **Gemini API key**: Configured under `GOOGLE_API_KEY`.
- **Supabase PostgreSQL connection**: Connection string pointing to Supabase hosting.
- **Model Selection**: Set to `gemini-flash-lite-latest` to avoid strict API key quota restrictions.

## Developer Setup in VS Code

If you see red squiggly lines on imports (like `sqlalchemy` or `langchain`), you need to tell VS Code to use the virtual environment interpreter:

1. Press **`Ctrl + Shift + P`** to open the Command Palette.
2. Select **`Python: Select Interpreter`**.
3. Choose the option pointing to `(.venv: venv)` or `.\.venv\Scripts\python.exe`.
4. If it doesn't apply immediately, run **`Developer: Reload Window`** in the Command Palette to reboot the VS Code Python extension.
