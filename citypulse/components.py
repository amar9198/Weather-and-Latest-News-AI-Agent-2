
"""HTML components for the CityPulse AI Streamlit app."""

import html
from urllib.parse import urlparse


def header_html(ready=True):
    """Render the main application header."""
    if ready:
        status = '<span style="color:#86efac;">● API keys configured</span>'
    else:
        status = '<span style="color:#f87171;">● API keys required</span>'

    return f"""
    <div style="
        padding:24px;
        margin:8px 0 18px;
        background:linear-gradient(135deg,#172554,#1e293b);
        border:1px solid #263247;
        border-radius:16px;
        color:#f8fafc;
    ">
        <h1 style="margin:0 0 12px;font-size:36px;">
            🌦️ CityPulse AI
        </h1>
        <p style="margin:0 0 14px;color:#cbd5e1;">
            Your intelligent city assistant
        </p>
        <div style="font-size:13px;font-weight:600;">{status}</div>
    </div>
    """


def service_row_html(name, configured, detail=""):
    """Render an API/service status row."""
    safe_name = html.escape(str(name))
    safe_detail = html.escape(str(detail or (
        "Configured" if configured else "Missing API key"
    )))

    if not configured:
        color = "#f87171"
    elif "failed" in safe_detail.lower() or "error" in safe_detail.lower():
        color = "#f87171"
    elif "configured" in safe_detail.lower():
        color = "#fbbf24"
    else:
        color = "#22c55e"

    return f"""
    <div style="
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:10px;
        padding:10px 12px;
        margin:6px 0;
        background:#111827;
        border:1px solid #263247;
        border-radius:10px;
    ">
        <span style="color:#e5e7eb;font-weight:600;">
            {safe_name}
        </span>
        <span style="color:{color};font-size:12px;">
            {safe_detail}
        </span>
    </div>
    """


def pill_html(text, color="#2563eb"):
    """Render a small status badge."""
    safe_text = html.escape(str(text))
    # Only allow known color formats; don't accept arbitrary CSS.
    allowed_colors = {
        "#2563eb", "#22c55e", "#f87171", "#f59e0b",
        "#64748b", "#dc2626",
    }
    safe_color = color if color in allowed_colors else "#2563eb"

    return f"""
    <span style="
        display:inline-block;
        padding:4px 10px;
        border-radius:999px;
        background:{safe_color};
        color:white;
        font-size:12px;
    ">{safe_text}</span>
    """


def tool_label(name):
    """Return (icon, display label), as expected by app.py."""
    labels = {
        "get_weather": ("🌦️", "Weather"),
        "fetch_weather": ("🌦️", "Weather"),
        "get_news": ("📰", "Latest News"),
        "fetch_news": ("📰", "Latest News"),
    }
    return labels.get(
        name,
        ("🔧", str(name).replace("_", " ").title()),
    )


def args_html(args):
    """Render tool arguments safely as a list."""
    if not isinstance(args, dict):
        args = {"Arguments": args}

    rows = "".join(
        f"<li><b>{html.escape(str(key))}:</b> "
        f"{html.escape(str(value))}</li>"
        for key, value in args.items()
    )

    return (
        '<ul style="color:#cbd5e1;margin:8px 0;padding-left:22px;">'
        f"{rows}</ul>"
    )


def approval_card_html(name, args):
    """Render a pending tool-approval card."""
    safe_name = html.escape(tool_label(name)[1])

    return f"""
    <div style="
        padding:14px;
        margin:8px 0;
        background:#172033;
        border:1px solid #475569;
        border-radius:12px;
    ">
        <h4 style="margin:0 0 8px;color:#f8fafc;">
            Tool approval required: {safe_name}
        </h4>
        {args_html(args)}
    </div>
    """


def weather_card_html(weather):
    """Render current weather details."""
    if not isinstance(weather, dict):
        weather = {"description": str(weather)}

    city = html.escape(str(weather.get("city", "Weather")))
    temp = html.escape(str(
        weather.get("temp", weather.get("temperature", "—"))
    ))
    desc = html.escape(str(
        weather.get("description", weather.get("desc", "No description"))
    ))
    humidity = html.escape(str(weather.get("humidity", "—")))
    wind = html.escape(str(weather.get("wind", "—")))

    return f"""
    <div style="
        padding:18px;
        background:#111827;
        border:1px solid #263247;
        border-radius:14px;
        color:#f8fafc;
    ">
        <h3 style="margin-top:0;">🌦️ {city}</h3>
        <div style="font-size:32px;font-weight:700;">{temp}°C</div>
        <p style="color:#cbd5e1;">{desc}</p>
        <p>💧 Humidity: {humidity}%</p>
        <p>💨 Wind: {wind} m/s</p>
    </div>
    """


def news_grid_html(articles):
    """Render news articles as styled HTML cards."""
    cards = []

    for article in articles or []:
        if not isinstance(article, dict):
            continue

        title = html.escape(str(article.get("title") or "Untitled"))
        content = html.escape(str(
            article.get("content") or "No summary available."
        ))
        url = str(article.get("url") or "").strip()

        parsed = urlparse(url)
        safe_url = (
            html.escape(url, quote=True)
            if parsed.scheme in ("http", "https") and parsed.netloc
            else ""
        )

        link_html = (
            f'<a href="{safe_url}" target="_blank" '
            'rel="noopener noreferrer" '
            'style="color:#93c5fd;">Read article ↗</a>'
            if safe_url else ""
        )

        cards.append(f"""
        <div style="
            padding:14px;
            margin:8px 0;
            background:#111827;
            border:1px solid #263247;
            border-radius:12px;
        ">
            <h4 style="color:#f8fafc;margin:0 0 8px;">
                {title}
            </h4>
            <p style="color:#cbd5e1;margin:0 0 10px;">
                {content}
            </p>
            {link_html}
        </div>
        """)

    if not cards:
        return '<p style="color:#cbd5e1;">No recent news found.</p>'

    return '<div class="news-grid">' + "\n".join(cards) + "</div>"
