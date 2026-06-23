import streamlit as st
import uuid
import asyncio  # New: Import asyncio is required
from intelligent_trade_agent import IntelligentTradeAgent

# --- Event Loop Management ---
# New: This is the crucial fix for running asyncio-based libraries like
# Google's GenAI SDK within Streamlit's threaded environment.
# This must be done BEFORE any library that needs an event loop is initialized.
try:
    # Try to get the running event loop in the current thread
    loop = asyncio.get_running_loop()
except RuntimeError:
    # If no loop is running, create a new one and set it for the current thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# -- Load agent only once
@st.cache_resource
def load_agent():
    """Loads the IntelligentTradeAgent instance."""
    print("--- Streamlit: Loading IntelligentTradeAgent via @st.cache_resource ---")
    return IntelligentTradeAgent()

# Now it is safe to load the agent
agent = load_agent()

# -- Set page config
st.set_page_config(page_title="Trade Chatbot", layout="wide")
st.title("🧠 LeAssistant")
st.caption("Ask anything about Import/Export Policies, HS Codes, or Foreign Trade Policy (FTP).")

# -- Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "input_key" not in st.session_state:
    st.session_state.input_key = str(uuid.uuid4())

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    print(f"--- New chat session started with Thread ID: {st.session_state.thread_id} ---")


# -- Basic Chat Bubble Styles
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
                <b>Assistant:</b><br>{content}
            </div>
            """,
            unsafe_allow_html=True
        )

# -- Display chat messages
for role, message in st.session_state.chat_history:
    render_message(role, message)

# -- User input form
# Using a form helps prevent reruns every time the user types a character
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "💬 Your message",
        key=st.session_state.input_key,
        placeholder="e.g., How do I export milk food for babies?"
    )
    submitted = st.form_submit_button("Send")

# -- On submit logic
if submitted and user_input.strip():
    # Append user message to history and render it immediately for better UX
    st.session_state.chat_history.append(("user", user_input))
    render_message("user", user_input)

    # Show a spinner while the agent is working
    with st.spinner("🤖 Agent is thinking..."):
        try:
            # Call the agent's invoke method with the user input and session's thread_id
            response = agent.invoke(user_input, thread_id=st.session_state.thread_id)
        except Exception as e:
            response = f"❌ An unexpected error occurred: {e}"
            st.error(response) # Display error prominently

    # Append agent's response to history and render it
    st.session_state.chat_history.append(("agent", response))
    render_message("agent", response)

    # Reset the input key to clear the text input field reliably
    st.session_state.input_key = str(uuid.uuid4())
    # We need to rerun to ensure the form is cleared after processing
    st.rerun()