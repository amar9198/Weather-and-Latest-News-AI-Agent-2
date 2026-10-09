import os
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from tavily import TavilyClient

load_dotenv()

st.set_page_config(page_title="City Agent", page_icon="🏙️", layout="centered")


# =========================
# Tools
# =========================
@tool
def get_weather(city: str) -> str:
    """Get current weather of a city"""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={api_key}&units=metric"
    data = requests.get(url, timeout=15).json()

    if str(data.get("cod")) != "200":
        return f"Error: {data.get('message', 'Could not fetch weather')}"

    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]
    return f"Weather in {city}: {desc}, {temp}°C"


@tool
def get_news(city: str) -> str:
    """Get latest news about a city"""
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(
        query=f"latest news in {city}", search_depth="basic", max_results=3
    )
    results = response.get("results", [])
    if not results:
        return f"No news found for {city}"

    items = []
    for r in results:
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "")
        items.append(f"- {title}\n  🔗 {url}\n  📝 {snippet[:100]}...")
    return f"Latest news in {city}:\n\n" + "\n\n".join(items)


# =========================
# Agent (cached so the checkpointer survives Streamlit reruns)
# =========================
@st.cache_resource
def build_agent(model: str, require_approval: bool):
    llm = ChatGroq(model=model, temperature=0)
    # Pauses the agent before each listed tool so the UI can ask the human.
    middleware = (
        [HumanInTheLoopMiddleware(interrupt_on={"get_weather": True, "get_news": True})]
        if require_approval
        else []
    )
    return create_agent(
        llm,
        tools=[get_weather, get_news],
        system_prompt="you are a helpful city assistant.",
        middleware=middleware,
        checkpointer=InMemorySaver(),
    )


# =========================
# Session state
# =========================
def reset_chat():
    st.session_state.messages = []
    st.session_state.pending = None
    st.session_state.thread_id = str(uuid.uuid4())


if "messages" not in st.session_state:
    reset_chat()

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.header("⚙️ Settings")
    model = st.selectbox(
        "Groq model",
        ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"],
    )
    require_approval = st.toggle(
        "Require approval for tool calls",
        value=True,
        help="Turn off to let the agent run tools without asking.",
    )
    if st.button("🗑️ New chat", use_container_width=True):
        reset_chat()
        st.rerun()

    st.divider()
    st.caption("API keys (from `.env`)")
    for key in ["GROQ_API_KEY", "TAVILY_API_KEY", "OPENWEATHER_API_KEY"]:
        st.write(f"{key}:", "✅" if os.getenv(key) else "❌ missing")

agent = build_agent(model, require_approval)
config = {"configurable": {"thread_id": st.session_state.thread_id}}


# =========================
# Helpers
# =========================
def collect_tool_activity(result):
    """Tool outputs produced during the latest turn."""
    msgs = result["messages"]
    last_human = max(
        (i for i, m in enumerate(msgs) if isinstance(m, HumanMessage)), default=0
    )
    return [
        {"name": m.name, "content": m.content}
        for m in msgs[last_human:]
        if isinstance(m, ToolMessage)
    ]


def handle_result(result):
    if result.get("__interrupt__"):
        st.session_state.pending = result["__interrupt__"][0].value
        return
    st.session_state.pending = None
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["messages"][-1].content,
            "tools": collect_tool_activity(result),
        }
    )


def run_agent(payload):
    try:
        with st.spinner("Thinking..."):
            result = agent.invoke(payload, config=config)
        handle_result(result)
    except Exception as e:
        st.session_state.pending = None
        st.session_state.messages.append(
            {"role": "assistant", "content": f"⚠️ Something went wrong: `{e}`"}
        )


# =========================
# Main UI
# =========================
st.title("🏙️ City Agent")
st.caption("Ask about the weather or latest news in any Indian city.")

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for t in msg.get("tools", []):
            with st.expander(f"🛠️ Tool used: {t['name']}"):
                st.text(t["content"])

# Pending approval card
pending = st.session_state.pending
if pending:
    with st.chat_message("assistant"):
        st.markdown("**The agent wants to use a tool. Approve?**")
        with st.form("approval_form"):
            choices = []
            for i, action in enumerate(pending["action_requests"]):
                st.markdown(f"🔧 `{action['name']}`")
                st.json(action["args"])
                choices.append(
                    st.radio(
                        "Decision",
                        ["Approve", "Reject"],
                        horizontal=True,
                        key=f"decision_{i}",
                        label_visibility="collapsed",
                    )
                )
            submitted = st.form_submit_button("Submit", type="primary")

    if submitted:
        decisions = [
            {"type": "approve"}
            if c == "Approve"
            else {"type": "reject", "message": "Tool call denied by user."}
            for c in choices
        ]
        run_agent(Command(resume={"decisions": decisions}))
        st.rerun()

# Chat input (disabled while waiting for an approval decision)
prompt = st.chat_input(
    "e.g. What's the weather in Kanpur?", disabled=bool(st.session_state.pending)
)
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    run_agent({"messages": [{"role": "user", "content": prompt}]})
    st.rerun()