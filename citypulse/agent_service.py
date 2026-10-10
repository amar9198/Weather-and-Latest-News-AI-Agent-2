
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_core.tools import tool

from citypulse import tools as city_tools

load_dotenv()


@dataclass
class TurnResult:
    reply: str = ""
    pending: list = field(default_factory=list)
    tools: list = field(default_factory=list)


# Conversation state for the current Streamlit process.
_conversations = {}


def make_llm(model):
    """Create the Groq chat model."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from your .env file.")

    return ChatGroq(
        model=model,
        temperature=0,
        api_key=api_key,
    )


@tool
def get_weather(city: str) -> str:
    """Get current weather conditions for a city in India."""
    return str(city_tools.fetch_weather(city))


@tool
def get_news(city: str) -> str:
    """Search for the latest news about a city in India."""
    return str(city_tools.fetch_news(city, 3))


TOOL_MAP = {
    "get_weather": get_weather,
    "get_news": get_news,
}


def build_agent(llm):
    """Attach the available tools to the language model."""
    return llm.bind_tools(list(TOOL_MAP.values()))


def friendly_error(exc):
    """Return a readable error without exposing credentials."""
    message = str(exc)

    for key in ("GROQ_API_KEY", "OPENWEATHER_API_KEY", "TAVILY_API_KEY"):
        secret = os.getenv(key, "")
        if secret:
            message = message.replace(secret, "[REDACTED]")

    if "401" in message or "authentication" in message.lower():
        return "Authentication failed. Please check your API key."
    if "429" in message or "rate limit" in message.lower():
        return "The AI service rate limit was reached. Please try again shortly."

    return message[:500] or "An unexpected error occurred."


def _call_model(agent, thread_id):
    """Invoke the model and return either a pending approval or a final reply."""
    state = _conversations[thread_id]
    response = agent.invoke(state["messages"])
    state["messages"].append(response)

    calls = getattr(response, "tool_calls", None) or []

    if calls:
        pending = [
            {
                "name": call["name"],
                "args": call.get("args", {}),
                "id": call.get("id", ""),
            }
            for call in calls
        ]
        state["pending_calls"] = calls
        return TurnResult(pending=pending)

    state["pending_calls"] = []
    return TurnResult(reply=response.content or "")


def start_turn(agent, thread_id, text):
    """Start a user turn and pause if the model requests tools."""
    state = _conversations.setdefault(
        thread_id,
        {"messages": [], "pending_calls": [], "tool_history": []},
    )

    if state["pending_calls"]:
        raise ValueError("Resolve the pending tool approvals before starting another turn.")

    state["messages"].append(HumanMessage(content=text))
    return _call_model(agent, thread_id)


def resume_turn(agent, thread_id, decisions):
    """Execute only approved calls; rejected calls are never executed."""
    state = _conversations.get(thread_id)

    if not state or not state["pending_calls"]:
        raise ValueError("No pending tool calls were found. Start a new message.")

    calls = state["pending_calls"]
    if len(decisions) != len(calls):
        raise ValueError("The number of decisions does not match the pending tool calls.")

    completed_tools = []

    for call, decision in zip(calls, decisions):
        name = call["name"]
        args = call.get("args", {})
        call_id = call.get("id", "")

        if decision not in ("approve", "reject"):
            raise ValueError("Each tool decision must be 'approve' or 'reject'.")

        if decision == "reject":
            content = "The user rejected this tool call. Do not attempt it again."
            status = "rejected"
        else:
            function = TOOL_MAP.get(name)
            if function is None:
                content = f"Tool '{name}' is not available."
                status = "rejected"
            else:
                try:
                    content = str(function.invoke(args))
                    status = "completed"
                except Exception as exc:
                    content = friendly_error(exc)
                    status = "error"

        state["messages"].append(
            ToolMessage(content=content, tool_call_id=call_id)
        )

        completed_tools.append({
            "name": name,
            "status": status,
            "args": args,
            "content": content,
        })

    state["pending_calls"] = []

    # Let the model interpret tool results and formulate a response.
    result = _call_model(agent, thread_id)
    result.tools = completed_tools
    return result
