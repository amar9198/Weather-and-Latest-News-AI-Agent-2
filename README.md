# 🌦️ Weather and Latest News AI Agent

An AI-powered application that combines weather updates and the latest news using **Python, Streamlit, LangChain, and Large Language Models (LLMs)**. The project aims to make it easier to access weather information and news summaries through a simple, interactive interface.

## 🚀 Live Demo

🔗 **Try the application:** https://weather-and-latest-news-ai-agent-2-eyq7p3epgtargchmtpcuxd.streamlit.app/

💻 **GitHub Repository:** https://github.com/amar9198/Weather-and-Latest-News-AI-Agent-2

## ✨ Features

- 🌤️ **Weather Information:** Retrieve weather information for a specified location.
- 📰 **Latest News:** Access recent news through integrated news-search tools.
- 🤖 **AI-Powered Responses:** Use language models to process user queries and generate helpful responses.
- 🔗 **LangChain Integration:** Connect language models with tools and external data sources.
- 🔍 **Web Search:** Integrate Tavily for web search capabilities.
- 💬 **Interactive Interface:** Use Streamlit to interact with the application.
- 🔐 **Environment-Based Configuration:** Keep API credentials in environment variables or Streamlit secrets.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web application |
| LangChain | LLM orchestration and tool integration |
| LangChain Core | Core abstractions and components |
| LangChain Community | Community integrations |
| LangChain Groq | Groq LLM integration |
| LangChain HuggingFace | Hugging Face integrations |
| LangChain Chroma | Vector database integration |
| Sentence Transformers | Text embeddings |
| ChromaDB | Vector storage and retrieval |
| Tavily | Web search integration |
| Requests | HTTP requests |
| python-dotenv | Environment variable management |

## 📂 Project Structure

```text
Weather-and-Latest-News-AI-Agent-2/
│
├── citypulse/             # Weather and related application modules
├── app.py                 # Streamlit application entry point
├── Agents.py               # Agent-related logic
├── city_agent_app.py       # City agent application module
├── newssummarizer.py       # News summarization module
├── toolcalling.py          # Tool-calling logic
├── requirements.txt        # Python dependencies
├── .gitignore              # Git exclusion rules
└── README.md               # Project documentation
```

*Note: The structure above describes the main files currently listed in the repository; individual module responsibilities may vary with implementation.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/amar9198/Weather-and-Latest-News-AI-Agent-2.git
cd Weather-and-Latest-News-AI-Agent-2
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and add the API keys required by your implementation.

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Get your API credentials from:

- Groq: https://console.groq.com/
- Tavily: https://tavily.com/

Use the exact environment variable names expected by your source code. Never commit your `.env` file or expose API keys publicly.

### 5. Run the application

```bash
streamlit run app.py
```

The application should open in your browser at the local URL displayed in the terminal, usually `http://localhost:8501`.

## ☁️ Deployment

The application is deployed using **Streamlit Community Cloud**.

Live application: https://weather-and-latest-news-ai-agent-2-eyq7p3epgtargchmtpcuxd.streamlit.app/

To deploy your own version:

1. Fork or push the project to GitHub.
2. Open https://share.streamlit.io/.
3. Connect your GitHub repository.
4. Select the appropriate branch and `app.py` as the entry point.
5. Configure the required API keys in the application's Secrets settings.
6. Deploy the application.

## 🔒 Security

- Store API keys in `.env` locally and Streamlit Secrets in production.
- Keep `.env`, `.venv/`, and `.streamlit/secrets.toml` out of Git.
- Avoid hardcoding API credentials in source files.
- Validate external API responses and handle network failures appropriately.

## 🎯 Project Goals

This project explores the practical use of AI agents, language models, tool calling, external APIs, and web search to build an application that brings weather information and news discovery together in one place.

## 🔮 Future Improvements

- Add a more detailed weather forecast.
- Provide news summaries by category and location.
- Improve error handling and API availability checks.
- Add conversation history and personalized queries.
- Enhance the user interface and mobile responsiveness.

## 👨‍💻 Author

**Amar Prajapati**

GitHub: https://github.com/amar9198

---

⭐ If you find this project interesting, consider giving the repository a star!

*Built with Python, Streamlit, LangChain, and AI.*
