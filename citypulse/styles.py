CSS = """
<style>
/* Main application */
.stApp {
    background-color: #0b1020;
    color: #f1f5f9;
}

[data-testid="stAppViewContainer"] {
    background-color: #0b1020;
}

[data-testid="stHeader"] {
    background-color: rgba(11, 16, 32, 0.95);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #263247;
}

[data-testid="stSidebar"] * {
    color: #f1f5f9;
}

/* Headings and text */
h1, h2, h3, h4, p, label {
    color: #f1f5f9;
}

/* Input fields */
.stTextInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stChatInput textarea {
    background-color: #1f2937;
    color: #f1f5f9;
    border: 1px solid #374151;
    border-radius: 8px;
}

/* Buttons */
.stButton > button,
.stFormSubmitButton > button {
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #3b82f6;
    border-radius: 8px;
    min-height: 40px;
    transition: background-color 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background-color: #1d4ed8;
    color: #ffffff;
    border-color: #60a5fa;
}

/* Main hero section */
.hero {
    padding: 24px;
    margin: 8px 0 20px;
    background: linear-gradient(135deg, #172554, #1e1b4b);
    border: 1px solid #263247;
    border-radius: 16px;
}

.hero h2 {
    margin-top: 0;
    font-size: 30px;
}

.hero p {
    color: #cbd5e1;
    margin-bottom: 0;
}

/* Section titles */
.section-title {
    font-size: 23px;
    font-weight: 700;
    margin: 22px 0 12px;
    color: #f8fafc;
}

/* Cards */
.glass {
    padding: 18px;
    margin: 12px 0;
    background: #111827;
    border: 1px solid #263247;
    border-radius: 14px;
}

.empty {
    text-align: center;
    padding: 36px 18px;
}

.empty .big {
    font-size: 42px;
    margin-bottom: 8px;
}

/* Sidebar branding */
.sb-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0 20px;
}

.sb-logo {
    font-size: 32px;
}

.sb-name {
    font-size: 21px;
    font-weight: 800;
    color: #f8fafc;
}

.sb-tag {
    font-size: 12px;
    color: #94a3b8;
}

.sb-label {
    margin: 22px 0 8px;
    color: #94a3b8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

.sb-about {
    color: #cbd5e1;
    font-size: 12px;
    line-height: 1.7;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: #111827;
    border: 1px solid #263247;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 12px;
}

/* Expanders */
[data-testid="stExpander"] {
    background-color: #111827;
    border: 1px solid #263247;
    border-radius: 10px;
}

/* Links */
a {
    color: #60a5fa;
}

a:hover {
    color: #93c5fd;
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Keep layout readable on smaller screens */
@media (max-width: 768px) {
    .hero h2 {
        font-size: 24px;
    }

    .section-title {
        font-size: 20px;
    }
}
</style>
"""