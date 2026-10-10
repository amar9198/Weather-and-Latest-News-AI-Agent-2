"""CityPulse AI — Weather, news, and an approval-gated AI assistant."""
import html
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
st.set_page_config(
    page_title="CityPulse AI",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)
from citypulse import agent_service, config, tools
from citypulse import components as ui
from citypulse.styles import CSS
# ============================================================
# Configuration
# ============================================================
try:
    config.apply_streamlit_secrets()
except Exception:
    pass
st.markdown(CSS, unsafe_allow_html=True)
AVATAR = {"user": "🧑", "assistant": "🌆"}
VIEWS = [
    ("overview", "🏠 Dashboard"),
    ("weather", "🌦️ Weather"),
    ("news", "📰 Latest News"),
    ("chat", "💬 Ask AI"),
]
# ============================================================
# Session state
# ============================================================
def init_state():
    defaults = {
        "view": "overview",
        "city_data": None,
        "recent": [],
        "messages": [],
        "pending": None,
        "decisions": {},
        "work": None,
        "model": config.DEFAULT_MODEL,
        "service": {"weather": None, "news": None, "ai": None},
        "search_request": None,
        "city_input": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            if isinstance(value, (dict, list)):
                st.session_state[key] = value.copy()
            else:
                st.session_state[key] = value
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
init_state()
ss = st.session_state
@st.cache_resource(show_spinner=False)
def get_agent(model):
    """Build and cache the tool-enabled AI agent."""
    llm = agent_service.make_llm(model)
    return agent_service.build_agent(llm)
# ============================================================
# General helpers
# ============================================================
def safe_error(exc):
    """Show a helpful error without exposing credentials."""
    message = (
        f"Request failed ({type(exc).__name__}). "
        "Check your API keys, internet connection, and terminal logs."
    )
    try:
        return config.redact(message)
    except Exception:
        return message
import logging
logging.basicConfig(level=logging.INFO)
def service_call(function, *args):
    try:
        result = function(*args)
        logging.info("%s succeeded", function.__name__)
        return result, None
    except Exception as exc:
        logging.exception(
            "%s failed",
            getattr(function, "__name__", "service"),
        )
        return None, safe_error(exc)
def tool_label(name):
    labels = {
        "get_weather": ("🌦️", "Weather"),
        "fetch_weather": ("🌦️", "Weather"),
        "get_news": ("📰", "Latest News"),
        "fetch_news": ("📰", "Latest News"),
    }
    try:
        result = ui.tool_label(name)
        if isinstance(result, tuple) and len(result) == 2:
            return result
        return "🔧", str(result)
    except Exception:
        return labels.get(
            name,
            ("🔧", str(name).replace("_", " ").title()),
        )
def render_arguments(arguments):
    """Display tool arguments safely."""
    if not isinstance(arguments, dict):
        arguments = {"Arguments": arguments}
    items = []
    for key, value in arguments.items():
        items.append(
            "<li><b>"
            + html.escape(str(key))
            + ":</b> "
            + html.escape(str(value))
            + "</li>"
        )
    st.markdown(
        "<ul>" + "".join(items) + "</ul>",
        unsafe_allow_html=True,
    )
def render_status(status):
    colors = {
        "completed": "#15803d",
        "approved": "#15803d",
        "rejected": "#b91c1c",
        "error": "#b91c1c",
        "pending": "#a16207",
    }
    color = colors.get(status, "#475569")
    label = html.escape(str(status).title())
    st.markdown(
        f'<span style="background:{color};color:white;'
        f'padding:5px 11px;border-radius:20px;'
        f'font-size:12px;font-weight:600;">{label}</span>',
        unsafe_allow_html=True,
    )
def render_header():
    ready = True
    try:
        ready = not config.missing_keys()
    except Exception:
        pass
    status = (
        "All required API keys are configured"
        if ready
        else "Some API keys are missing"
    )
    status_color = "#4ade80" if ready else "#fca5a5"
    st.markdown(
        f"""
        <div style="
            padding:24px;
            margin:5px 0 22px;
            background:linear-gradient(120deg,#172554,#111827);
            border:1px solid #334155;
            border-radius:18px;
        ">
            <h1 style="margin:0;color:#f8fafc;">
                🌦️ CityPulse AI
            </h1>
            <p style="color:#cbd5e1;margin:8px 0 0;">
                Your intelligent city assistant for weather, news and AI.
            </p>
            <p style="color:{status_color};font-size:13px;margin-bottom:0;">
                ● {html.escape(status)}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
# ============================================================
# Navigation and chat callbacks
# ============================================================
def goto(view):
    ss.view = view
def reset_conversation():
    ss.messages = []
    ss.pending = None
    ss.decisions = {}
    ss.work = None
    ss.thread_id = str(uuid.uuid4())
def new_conversation():
    reset_conversation()
    ss.view = "chat"
def request_search(city):
    ss.city_input = city
    ss.search_request = city
    if ss.view == "chat":
        ss.view = "overview"
def ask(question):
    question = " ".join(str(question).split())[:2000]
    if not question or ss.pending or ss.work:
        return
    ss.messages.append({
        "role": "user",
        "content": question,
    })
    ss.work = {
        "type": "start",
        "text": question,
    }
    ss.view = "chat"
def finalize_decisions():
    if not ss.pending:
        return
    if all(
        index in ss.decisions
        for index in range(len(ss.pending))
    ):
        ss.work = {
            "type": "resume",
            "decisions": [
                ss.decisions[index]
                for index in range(len(ss.pending))
            ],
        }
        ss.pending = None
        ss.decisions = {}
def decide(index, decision):
    if ss.pending and decision in ("approve", "reject"):
        ss.decisions[index] = decision
        finalize_decisions()
def decide_all(decision):
    if ss.pending and decision in ("approve", "reject"):
        for index in range(len(ss.pending)):
            ss.decisions.setdefault(index, decision)
        finalize_decisions()
# ============================================================
# Sidebar
# ============================================================
def service_state(key_name, service_name):
    try:
        configured = config.key_configured(key_name)
    except Exception:
        configured = False
    if not configured:
        return False, "Key missing"
    last_status = ss.service.get(service_name)
    if last_status == "ok":
        return True, "Last call successful"
    if last_status == "error":
        return True, "Last call failed"
    return True, "Configured"
def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:8px 0 18px;">
                <div style="font-size:25px;font-weight:750;">
                    🌦️ CityPulse AI
                </div>
                <div style="color:#94a3b8;font-size:13px;">
                    Weather · News · AI assistant
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "＋ New conversation",
            key="side_new",
            on_click=new_conversation,
            use_container_width=True,
        )
        st.markdown("#### QUICK ACTIONS")
        for key, label in VIEWS:
            st.button(
                label,
                key=f"nav_{key}",
                on_click=goto,
                args=(key,),
                type="primary" if ss.view == key else "secondary",
                use_container_width=True,
            )
        if ss.recent:
            st.markdown("#### RECENT CITIES")
            for index, city in enumerate(ss.recent):
                st.button(
                    f"📍 {city}",
                    key=f"recent_{index}",
                    on_click=request_search,
                    args=(city,),
                    use_container_width=True,
                )
        st.markdown("#### SETTINGS")
        models = getattr(config, "MODELS", [config.DEFAULT_MODEL])
        if not models:
            models = [config.DEFAULT_MODEL]
        if ss.model not in models:
            ss.model = models[0]
        st.selectbox(
            "AI model",
            options=models,
            key="model",
            disabled=bool(ss.pending or ss.work),
        )
        st.markdown("#### SERVICES")
        services = [
            ("AI assistant (Groq)", "GROQ_API_KEY", "ai"),
            ("Weather (OpenWeather)", "OPENWEATHER_API_KEY", "weather"),
            ("News (Tavily)", "TAVILY_API_KEY", "news"),
        ]
        for name, key_name, service_name in services:
            configured, detail = service_state(
                key_name,
                service_name,
            )
            try:
                row = ui.service_row_html(
                    name,
                    configured,
                    detail,
                )
                st.markdown(row, unsafe_allow_html=True)
            except Exception:
                color = "#4ade80" if configured else "#f87171"
                st.markdown(
                    f"""
                    <div style="
                        padding:10px;
                        margin:6px 0;
                        background:#111827;
                        border:1px solid #334155;
                        border-radius:10px;
                        display:flex;
                        justify-content:space-between;
                        gap:8px;
                    ">
                        <span>{html.escape(name)}</span>
                        <span style="color:{color};">
                            {html.escape(detail)}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.caption(
            "Service status shows whether keys are configured "
            "and whether recent requests succeeded."
        )
        st.markdown("#### ABOUT")
        st.caption(
            "Python · Streamlit · LangChain · Groq · "
            "OpenWeatherMap · Tavily"
        )
# ============================================================
# Weather and news retrieval
# ============================================================
def run_search(city):
    city = " ".join(str(city).split())[:80]
    if not city:
        return
    with st.spinner(f"Fetching live weather and news for {city}..."):
        with ThreadPoolExecutor(max_workers=2) as pool:
            weather_future = pool.submit(
                service_call,
                tools.fetch_weather,
                city,
            )
            news_future = pool.submit(
                service_call,
                tools.fetch_news,
                city,
                getattr(config, "DASHBOARD_NEWS_RESULTS", 5),
            )
            weather, weather_error = weather_future.result()
            news, news_error = news_future.result()
    ss.service["weather"] = (
        "ok" if weather is not None else "error"
    )
    ss.service["news"] = (
        "ok" if news is not None else "error"
    )
    ss.city_data = {
        "query": city,
        "weather": weather,
        "weather_error": weather_error,
        "news": news,
        "news_error": news_error,
        "fetched_at": time.strftime("%d %b %Y, %H:%M"),
    }
    if weather is not None or news is not None:
        actual_city = (weather or {}).get("city") or city
        ss.recent = [actual_city] + [
            old for old in ss.recent
            if old.lower() != actual_city.lower()
        ]
        ss.recent = ss.recent[:6]
def render_search_box():
    """Render the search form and normalize common natural-language queries."""
    requested_city = ss.pop("search_request", None)
    with st.form("city_form", border=False):
        col_input, col_button = st.columns(
            [5, 1.2],
            vertical_alignment="center",
        )
        city = col_input.text_input(
            "City",
            key="city_input",
            placeholder="Search a city, e.g. Kanpur",
            label_visibility="collapsed",
        )
        submitted = col_button.form_submit_button(
            "🔍 Search",
            type="primary",
            use_container_width=True,
        )
    suggested = getattr(
        config,
        "SUGGESTED_CITIES",
        ["Kanpur", "Lucknow", "Delhi", "Mumbai", "Agra"],
    )
    columns = st.columns(max(1, len(suggested)))
    for column, city_name in zip(columns, suggested):
        column.button(
            city_name,
            key=f"chip_{city_name}",
            on_click=request_search,
            args=(city_name,),
            use_container_width=True,
        )
    if submitted:
        if not city.strip():
            st.error("Please enter a city name.")
            return
        requested_city = city
    if not requested_city:
        return
    cleaned_city = " ".join(str(requested_city).split()).strip(" ,.!?")
    if not cleaned_city:
        st.error("Please enter a valid city name, such as Lucknow.")
        return
    # Remove common natural-language prefixes, including "weather of Lucknow".
    prefix_patterns = [
        r"^(?:please\s+)?",
        r"^(?:show\s+me\s+)",
        r"^(?:what(?:'s|\s+is)\s+)",
        r"^(?:tell\s+me\s+)",
        r"^(?:the\s+)?(?:current\s+)?(?:weather|temperature|forecast)\s+(?:of|in|for|at)\s+",
        r"^(?:the\s+)?(?:latest\s+)?(?:local\s+)?news\s+(?:of|in|for|about)\s+",
        r"^(?:weather|temperature|forecast)\s+",
        r"^(?:latest\s+)?news\s+",
    ]
    changed = True
    while changed:
        changed = False
        for pattern in prefix_patterns:
            updated = re.sub(pattern, "", cleaned_city, count=1, flags=re.IGNORECASE).strip()
            if updated != cleaned_city:
                cleaned_city = updated
                changed = True
                break
    # Remove common trailing request words (e.g. "Lucknow weather").
    cleaned_city = re.sub(
        r"\s+(?:current\s+)?(?:weather|temperature|forecast|latest\s+news|news)$",
        "",
        cleaned_city,
        flags=re.IGNORECASE,
    ).strip(" ,.!?")
    if not cleaned_city:
        st.error("Please enter a city name, such as Lucknow.")
        return
    run_search(cleaned_city)
def render_weather_section(data):
    st.markdown("### 🌦️ Current weather")
    weather = data.get("weather")
    if not weather:
        st.warning(
            data.get("weather_error")
            or "Weather is unavailable right now."
        )
        return
    try:
        st.markdown(
            ui.weather_card_html(weather),
            unsafe_allow_html=True,
        )
        return
    except Exception:
        pass
    city = html.escape(str(weather.get("city", data["query"])))
    temperature = weather.get(
        "temp",
        weather.get("temperature", "—"),
    )
    description = html.escape(
        str(weather.get("description", weather.get("desc", "Unavailable")))
    )
    humidity = weather.get("humidity", "—")
    wind = weather.get("wind", "—")
    st.markdown(
        f"""
        <div style="
            padding:24px;
            background:linear-gradient(120deg,#172554,#111827);
            border:1px solid #334155;
            border-radius:16px;
            color:#f8fafc;
        ">
            <h3>{city}</h3>
            <div style="font-size:40px;font-weight:750;">
                {html.escape(str(temperature))}°C
            </div>
            <p>{description}</p>
            <p>💧 Humidity: {html.escape(str(humidity))}%</p>
            <p>💨 Wind: {html.escape(str(wind))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
# ============================================================
# News section
# ============================================================
def render_news_section(data):
    st.markdown("### 📰 Latest news")
    articles = data.get("news")
    if not articles:
        if data.get("news_error"):
            st.warning(data["news_error"])
        else:
            st.info(
                f"No recent news results were found for {data['query']}."
            )
        return
    try:
        news_html = ui.news_grid_html(articles)
        st.html(news_html)
        return
    except Exception:
        pass
    for article in articles:
        title = str(article.get("title") or "Untitled")
        content = str(
            article.get("content")
            or article.get("snippet")
            or "No summary available."
        )
        url = str(article.get("url") or "")
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.write(content)
            if url.startswith(("https://", "http://")):
                st.link_button(
                    "Read article ↗",
                    url,
                    use_container_width=False,
                )
# ============================================================
# Dashboard
# ============================================================
def render_dashboard(show_weather=True, show_news=True):
    if ss.view == "overview":
        st.markdown(
            """
            <div style="padding:6px 0 18px;">
                <h2>Know your city in seconds</h2>
                <p>
                    Live weather, the latest local headlines, and an AI
                    assistant that asks before using tools.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    render_search_box()
    data = ss.city_data
    if not data:
        st.markdown(
            """
            <div style="
                padding:28px;
                margin-top:12px;
                background:#111827;
                border:1px solid #263247;
                border-radius:16px;
                text-align:center;
            ">
                <div style="font-size:42px;">🏙️</div>
                <h3>Pick a city to get started</h3>
                <p>
                    Search above or choose a suggested city to see
                    live weather and recent news.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    weather = data.get("weather")
    display_city = (weather or {}).get("city") or data["query"]
    st.caption(
        f"Showing results for {display_city} · "
        f"Updated {data['fetched_at']}"
    )
    if show_weather:
        render_weather_section(data)
    if show_news:
        render_news_section(data)
    if weather or data.get("news"):
        st.button(
            f"💬 Ask AI about {display_city}",
            key="ask_about_city",
            on_click=ask,
            args=(
                f"Give me a quick weather and news briefing for {display_city}.",
            ),
            disabled=bool(ss.pending or ss.work),
        )
# ============================================================
# Chat rendering
# ============================================================
def render_message(message):
    role = message.get("role", "assistant")
    if role not in AVATAR:
        role = "assistant"
    with st.chat_message(role, avatar=AVATAR[role]):
        st.markdown(str(message.get("content", "")))
        for result in message.get("tools", []):
            icon, label = tool_label(result.get("name", "tool"))
            status = result.get("status", "completed")
            with st.expander(f"{icon} {label} · {status.title()}"):
                render_status(status)
                render_arguments(result.get("args") or {})
                if status in ("completed", "error"):
                    st.write(result.get("content", ""))
                elif status == "rejected":
                    st.caption(
                        "You rejected this tool call. It was not run."
                    )
def render_pending():
    if not ss.pending:
        return
    with st.chat_message("assistant", avatar=AVATAR["assistant"]):
        st.markdown("### The assistant wants to use a tool")
        st.write("Review each request and approve or reject it.")
        for index, action in enumerate(ss.pending):
            decision = ss.decisions.get(index)
            status = {
                "approve": "approved",
                "reject": "rejected",
            }.get(decision, "pending")
            icon, label = tool_label(action.get("name", "tool"))
            with st.container(border=True):
                st.markdown(f"**{icon} {label}**")
                render_arguments(action.get("args") or {})
                render_status(status)
                if decision is None:
                    left, right = st.columns(2)
                    left.button(
                        "✅ Approve",
                        key=f"approve_{ss.thread_id}_{index}",
                        on_click=decide,
                        args=(index, "approve"),
                        type="primary",
                        use_container_width=True,
                    )
                    right.button(
                        "❌ Reject",
                        key=f"reject_{ss.thread_id}_{index}",
                        on_click=decide,
                        args=(index, "reject"),
                        use_container_width=True,
                    )
        if len(ss.pending) > 1:
            left, right = st.columns(2)
            left.button(
                "Approve all",
                key=f"approve_all_{ss.thread_id}",
                on_click=decide_all,
                args=("approve",),
                use_container_width=True,
            )
            right.button(
                "Reject all",
                key=f"reject_all_{ss.thread_id}",
                on_click=decide_all,
                args=("reject",),
                use_container_width=True,
            )
        st.caption("A tool runs only after you approve it.")
# ============================================================
# AI agent processing
# ============================================================
def process_work(work):
    label = (
        "CityPulse AI is thinking..."
        if work["type"] == "start"
        else "Running approved tools..."
    )
    result = None
    error = None
    with st.chat_message("assistant", avatar=AVATAR["assistant"]):
        with st.spinner(label):
            try:
                agent = get_agent(ss.model)
                if work["type"] == "start":
                    result = agent_service.start_turn(
                        agent,
                        ss.thread_id,
                        work["text"],
                    )
                else:
                    result = agent_service.resume_turn(
                        agent,
                        ss.thread_id,
                        work["decisions"],
                    )
                ss.service["ai"] = "ok"
            except Exception as exc:
                try:
                    error = agent_service.friendly_error(exc)
                except Exception:
                    error = safe_error(exc)
                ss.service["ai"] = "error"
    if error:
        ss.messages.append({
            "role": "assistant",
            "content": f"⚠️ {error}",
        })
    elif result is not None and getattr(result, "pending", None):
        ss.pending = result.pending
        ss.decisions = {}
    elif result is not None:
        ss.messages.append({
            "role": "assistant",
            "content": (
                getattr(result, "reply", None)
                or "I couldn't produce an answer. Please try again."
            ),
            "tools": getattr(result, "tools", None) or [],
        })
    st.rerun()
def render_chat():
    left, right = st.columns(
        [5, 1.5],
        vertical_alignment="center",
    )
    left.markdown("### 💬 AI City Assistant")
    right.button(
        "🗑️ Clear chat",
        key="clear_chat",
        on_click=reset_conversation,
        use_container_width=True,
    )
    try:
        groq_configured = config.key_configured("GROQ_API_KEY")
    except Exception:
        groq_configured = False
    if not groq_configured:
        st.warning(
            "GROQ_API_KEY is missing. Add it to your .env file "
            "to enable the AI assistant."
        )
    if not ss.messages and not ss.pending and not ss.work:
        st.markdown(
            """
            <div style="padding:12px 0;">
                <div style="font-size:36px;">🌆</div>
                <h3>Ask me about any city</h3>
                <p>
                    I can retrieve weather and recent news.
                    You decide whether each tool can run.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        suggestions = [
            "What is the weather in Kanpur?",
            "Show me the latest news about Delhi.",
            "Should I carry an umbrella today in Lucknow?",
            "Summarize the latest news in Mumbai.",
        ]
        first, second = st.columns(2)
        for index, suggestion in enumerate(suggestions):
            column = first if index % 2 == 0 else second
            column.button(
                suggestion,
                key=f"suggestion_{index}",
                on_click=ask,
                args=(suggestion,),
                use_container_width=True,
            )
    for message in ss.messages:
        render_message(message)
    render_pending()
    busy = bool(ss.pending) or ss.work is not None
    prompt = st.chat_input(
        "Approve or reject the pending tool first..."
        if ss.pending
        else "Ask about weather or news in any city...",
        disabled=busy,
    )
    if prompt and prompt.strip() and not busy:
        ask(prompt.strip())
        st.rerun()
    # Remove the queued job before processing to avoid duplicate execution.
    work = ss.work
    ss.work = None
    if work:
        process_work(work)
# ============================================================
# Main application
# ============================================================
def main():
    render_sidebar()
    render_header()
    try:
        missing = config.missing_keys()
    except Exception:
        missing = []
    if missing:
        st.warning(
            "Missing environment variables: "
            + ", ".join(str(key) for key in missing)
            + ". Add them to your .env file or Streamlit secrets."
        )
    if ss.view == "chat":
        render_chat()
    elif ss.view == "weather":
        render_dashboard(show_weather=True, show_news=False)
    elif ss.view == "news":
        render_dashboard(show_weather=False, show_news=True)
    else:
        render_dashboard(show_weather=True, show_news=True)
if __name__ == "__main__":
    main()
