"""
TradeMind AI — Intelligent Trade Agent
Author: Aditi
The main AI agent that combines SQL queries, RAG retrieval, and re-ranking
to answer questions about Indian trade policies, HS codes, and FTP schemes.
"""

import traceback
from sqlalchemy import create_engine, inspect
from langchain_community.utilities import SQLDatabase
from langchain_postgres.vectorstores import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from sentence_transformers.cross_encoder import CrossEncoder
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# Import centralized config
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Suppress Hugging Face Hub warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import logging
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


# Override print globally in this module to safely handle Windows Unicode console outputs
def print(*args, **kwargs):
    import builtins
    try:
        builtins.print(*args, **kwargs)
    except Exception:
        try:
            cleaned = [str(arg).encode('ascii', errors='replace').decode('ascii') for arg in args]
            builtins.print(*cleaned, **kwargs)
        except Exception:
            pass


class IntelligentTradeAgent:

    def __init__(self):
        print("--- Initializing Intelligent Trade Agent ---")
        self.connection_string = config.DB_CONNECTION_STRING
        self.ftp_collection_name = config.FTP_COLLECTION_NAME
        self.import_policy_collection_name = config.IMPORT_POLICY_COLLECTION_NAME
        self.export_policy_collection_name = config.EXPORT_POLICY_COLLECTION_NAME

        self._initialize_models()
        self.engine = self._create_db_engine()
        self.sql_tools = self._setup_dynamic_sql_toolkit(self.engine)

        # Set up vector retrievers for each policy domain
        self.ftp_retriever = self._setup_vector_retriever("FTP Policy", self.ftp_collection_name)
        self.import_policy_retriever = self._setup_vector_retriever("Import Policy Chapters", self.import_policy_collection_name)
        self.export_policy_retriever = self._setup_vector_retriever("Export Policy Chapters", self.export_policy_collection_name)

        # Create advanced RAG tools with metadata filtering support
        self.ftp_rag_tool = self._create_rag_tool(
            name="retrieve_foreign_trade_policy_context",
            description="Use for questions about general Foreign Trade Policy (FTP) rules, schemes (like EPCG), definitions, and procedures. Can optionally filter by 'chapter_no'.",
            retriever=self.ftp_retriever
        )
        self.import_policy_rag_tool = self._create_rag_tool(
            name="retrieve_import_policy_context",
            description="Use for broad questions about IMPORTING a specific category of goods. Use the 'chapter_no' argument for a precise, filtered search when the chapter is known.",
            retriever=self.import_policy_retriever
        )
        self.export_policy_rag_tool = self._create_rag_tool(
            name="retrieve_export_policy_context",
            description="Use for broad questions about EXPORTING a specific category of goods. Use the 'chapter_no' argument for a precise, filtered search when the chapter is known.",
            retriever=self.export_policy_retriever
        )

        self.tools = self.sql_tools + [self.import_policy_rag_tool, self.export_policy_rag_tool, self.ftp_rag_tool]

        self.checkpointer = MemorySaver()
        self._compile_graph()
        print("--- Agent Initialized Successfully ---\n")

    def _initialize_models(self):
        print("  -> Loading models...")
        self.llm = ChatGoogleGenerativeAI(model=config.LLM_MODEL, temperature=0)
        self.embeddings = GoogleGenerativeAIEmbeddings(model=config.EMBEDDING_MODEL, output_dimensionality=768)
        self.cross_encoder = CrossEncoder(config.CROSS_ENCODER_MODEL)
        print("    -> Models loaded.")

    def _create_db_engine(self):
        print("  -> Creating robust database engine...")
        return create_engine(self.connection_string, pool_size=5, max_overflow=2, pool_recycle=300)

    def _setup_vector_retriever(self, name: str, collection_name: str):
        print(f"  -> Setting up retriever for '{name}' (collection: {collection_name})")
        vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=collection_name,
            connection=self.engine,
        )
        return vector_store.as_retriever(search_kwargs={"k": 10})

    def _setup_dynamic_sql_toolkit(self, engine):
        print("  -> Setting up DYNAMIC SQL toolkit...")
        inspector = inspect(engine)
        usable_tables = [
            name for name in inspector.get_table_names()
            if not name.startswith(("langchain_pg_", "VectorDB"))
        ]
        print(f"    -> Agent will have access to: {usable_tables}")
        db = SQLDatabase(engine=engine, include_tables=usable_tables, sample_rows_in_table_info=2)
        toolkit = SQLDatabaseToolkit(db=db, llm=self.llm)
        all_sql_tools = toolkit.get_tools()
        print(f"    -> SQL toolkit created with {len(all_sql_tools)} tools.")
        return all_sql_tools

    def _create_rag_tool(self, name: str, description: str, retriever):
        print(f"  -> Creating ADVANCED RAG tool: {name}")

        def _rag_logic_with_filter(query: str, chapter_no: int = None) -> str:
            """
            Retrieve and re-rank policy texts. If a chapter_no is provided,
            it will pre-filter the search to only that chapter for higher accuracy.
            """
            print(f"---EXECUTING RAG TOOL '{name}' with query: '{query}' | Chapter Filter: {chapter_no}---")

            search_kwargs = {"k": 10}
            if chapter_no:
                search_kwargs["filter"] = {"chapter_no": chapter_no}
                print(f"  -> Applied metadata filter for chapter_no = {chapter_no}")

            filtered_retriever = retriever.vectorstore.as_retriever(
                search_kwargs=search_kwargs
            )
            retrieved_docs = filtered_retriever.invoke(query)

            if not retrieved_docs:
                return "No relevant documents found with the given filter."

            pairs = [[query, doc.page_content] for doc in retrieved_docs]
            scores = self.cross_encoder.predict(pairs)
            scored_docs = sorted(zip(scores, retrieved_docs), key=lambda x: x[0], reverse=True)
            top_n = 3
            re_ranked_docs = [doc for _, doc in scored_docs[:top_n]]
            print(f"  -> Selected top {len(re_ranked_docs)} documents after re-ranking.")

            context_parts = []
            for i, doc in enumerate(re_ranked_docs):
                metadata_str = ", ".join(f"{k}: {v}" for k, v in doc.metadata.items())
                context_parts.append(
                    f"--- Passage {i+1} ---\n"
                    f"Metadata: {metadata_str}\n"
                    f"Content: {doc.page_content}"
                )
            return "\n\n".join(context_parts)

        return StructuredTool.from_function(
            func=_rag_logic_with_filter,
            name=name,
            description=description,
        )

    def _compile_graph(self):
        print("  -> Compiling ReAct agent graph...")
        self.graph = create_react_agent(self.llm, self.tools, checkpointer=self.checkpointer)
        print("    -> Graph compiled.")

    def get_system_prompt(self):
        """
        Metadata-Aware & Case-Insensitive prompt that teaches the agent to use
        metadata filters for RAG and case-insensitive functions for SQL.
        """
        return """You are a specialized problem-solving assistant for Indian international trade, if user ask never reveal your true identity always say that you are TradeMind AI Assistant.

**YOUR CORE MISSION (THE WHY):**

Your primary mission is to provide a complete, actionable answer by combining specific data from the database with general rules from policy documents. The `chapter_no` is the golden key that links these two worlds.

---

**A PROVEN WORKFLOW (THE HOW):**

**STEP 1: TRIAGE - Determine Intent (Product vs. Policy)**
*   If the user asks about a **specific, tangible item** (e.g., "valves", "peas"), you MUST use the **"Product-Specific Workflow"**.
*   If the user asks about a **general rule or scheme** (e.g., "what is RoDTEP?"), use the appropriate RAG tool like `retrieve_foreign_trade_policy_context`.

---

**THE PRODUCT-SPECIFIC WORKFLOW (The most efficient path)**

*   **PART 1: DISCOVER the Product and Chapter in the Database**
    *   **Action:** Your first action is ALWAYS to find the item in the correct SQL table to get its HS Code and its `chapter_no`.
        *   **If IMPORTING:** Query `hs_codes_rodtep_import_policies_merged`.
        *   **If EXPORTING:** Query `hs_codes_rodtep_export_policies`.
    *   **Crucial Search Strategy:** The database is case-sensitive. To ensure you find the product, you **MUST** use the `LOWER()` function on both the column and the search term.
        *   *Example for an import search:* `sql_db_query(query="SELECT \"Tariff Lines / HS Code\", \"Description of Goods (As per CTH )\", chapter_no FROM hs_codes_rodtep_import_policies_merged WHERE LOWER(\"Description of Goods (As per CTH )\") ILIKE LOWER('%peas%')")`
    *   **If this SQL search fails, use the RAG tool *without* a filter as a fallback to find the `chapter_no` semantically.**

*   **PART 2: RETRIEVE Policy Context using the Metadata Filter**
    *   **Action:** Immediately after you identify the `chapter_no`, your **next mandatory step** is to get the high-level policy rules using that chapter number as a filter.
    *   **This is the most precise way to get context.** Call the RAG tool with the `chapter_no` argument.
    *   **How to do it:**
        *   If researching an **IMPORT**, call `retrieve_import_policy_context(query="general policy", chapter_no=THE_CHAPTER_NUMBER)`.
        *   If researching an **EXPORT**, call `retrieve_export_policy_context(query="general policy", chapter_no=THE_CHAPTER_NUMBER)`.

*   **STEP 3: SYNTHESIZE AND ANSWER**
    *   **Action:** Combine the information from Part 1 (SQL) and Part 2 (RAG) to formulate a complete answer.

---

**TOOL REFERENCE:**

*   **SQL Tools (`sql_db_...`)**: Your primary tool for finding specific products and their `chapter_no`. Remember to use `LOWER()` for searching and quotes for column names with spaces.
*   **RAG Tools (`retrieve_..._context`)**: This tool is now much more powerful. Use it with the `chapter_no` argument for a highly accurate, filtered search once you have identified the chapter.
"""

    def invoke(self, question: str, thread_id: str):
        config_dict = {"configurable": {"thread_id": thread_id}}
        print(f"\n{'='*50}\n--- Running Agent for thread '{thread_id}' ---\nQUESTION: {question}\n{'='*50}")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=question)
        ]

        import time
        final_answer = ""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Pass original inputs on attempt 0. On subsequent retry attempts, pass None
                # to instruct LangGraph to resume the existing checkpointed thread.
                inputs = {"messages": messages} if attempt == 0 else None
                events = self.graph.stream(inputs, config=config_dict, stream_mode="values")
                
                for event in events:
                    last_message = event["messages"][-1]
                    if isinstance(last_message, AIMessage) and last_message.tool_calls:
                        print("\n[Thinking] Agent is thinking... Tool called:")
                        try:
                            last_message.pretty_print()
                        except Exception:
                            pass
                    elif isinstance(last_message, ToolMessage):
                        print(f"\n[Tool] Tool '{last_message.name}' result:")
                        try:
                            last_message.pretty_print()
                        except Exception:
                            pass
                    elif isinstance(last_message, AIMessage) and not last_message.tool_calls:
                        content = last_message.content
                        if isinstance(content, list):
                            final_answer = "".join(
                                part.get("text", "") if isinstance(part, dict) else str(part)
                                for part in content
                            )
                        elif isinstance(content, dict):
                            final_answer = content.get("text", str(content))
                        else:
                            final_answer = str(content)
                        print("\n[Success] Final Answer:")
                        try:
                            last_message.pretty_print()
                        except Exception:
                            pass
                # Successful run, break out of attempt loop
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt < max_attempts - 1:
                        print(f"\n[Rate Limit] Hit Gemini API rate limit. Waiting 12 seconds before retrying (Attempt {attempt+1}/{max_attempts})...")
                        time.sleep(12)
                        continue
                
                print(f"\n[Error] ERROR: {e}")
                traceback.print_exc()
                final_answer = f"An error occurred: {e}"
                break
                
        return final_answer
