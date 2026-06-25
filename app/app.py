"""
TradeMind AI — Streamlit Chat Application
Author: Aditi
A beautiful chatbot UI for querying Indian trade policies, HS codes, and FTP schemes.
"""

import streamlit as st
import uuid
import asyncio
import sys
import os

# Add project root to path so we can import config and agents
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402 — loads API key into env
from agents.intelligent_trade_agent import IntelligentTradeAgent  # noqa: E402

# -- Set page config (MUST be the first Streamlit command)
st.set_page_config(page_title="TradeMind AI", layout="wide", page_icon="🧠")

st.title("🧠 TradeMind AI")
st.caption("Ask anything about Import/Export Policies, HS Codes, or Foreign Trade Policy (FTP).")

# --- Event Loop Management ---
# Required for running asyncio-based libraries like Google's GenAI SDK
# within Streamlit's threaded environment.
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# -- Load agent only once
@st.cache_resource
def load_agent():
    """Loads the IntelligentTradeAgent instance."""
    print("--- Streamlit: Loading IntelligentTradeAgent via @st.cache_resource ---")
    return IntelligentTradeAgent()

# Load the agent with a beautiful spinner so the user knows it's initializing
with st.spinner("Initializing AI Models & Database (this takes ~15 seconds on first run)..."):
    agent = load_agent()

# -- Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "input_key" not in st.session_state:
    st.session_state.input_key = str(uuid.uuid4())

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    print(f"--- New chat session started with Thread ID: {st.session_state.thread_id} ---")


# -- Chat Bubble Styles
def render_message(role, content):
    """Renders chat messages with custom styling."""
    if role == "user":
        st.markdown(
            f"""
            <div style='
                background-color: #E1F5FE;
                color: #01579B;
                padding: 12px 15px;
                border-radius: 10px 10px 0 10px;
                margin: 10px 0;
                max-width: 80%;
                margin-left: auto;
                font-size: 15px;
                border: 1px solid #B3E5FC;
            '>
                <b>You:</b> {content}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style='
                background-color: #FFFFFF;
                color: #333;
                padding: 12px 15px;
                border-radius: 10px 10px 10px 0;
                margin: 10px 0;
                max-width: 80%;
                margin-right: auto;
                font-size: 15px;
                border: 1px solid #E0E0E0;
            '>
                <b>TradeMind AI:</b><br>{content}
            </div>
            """,
            unsafe_allow_html=True
        )


# -- Display chat messages
for role, message in st.session_state.chat_history:
    render_message(role, message)

# -- User input form
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "💬 Your message",
        key=st.session_state.input_key,
        placeholder="e.g., How do I export milk food for babies?"
    )
    submitted = st.form_submit_button("Send")

# -- On submit logic
if submitted and user_input.strip():
    st.session_state.chat_history.append(("user", user_input))
    render_message("user", user_input)

    with st.spinner("🤖 Agent is thinking..."):
        try:
            response = agent.invoke(user_input, thread_id=st.session_state.thread_id)
        except Exception as e:
            response = f"❌ An unexpected error occurred: {e}"
            st.error(response)

    st.session_state.chat_history.append(("agent", response))
    render_message("agent", response)

    st.session_state.input_key = str(uuid.uuid4())
    st.rerun()
