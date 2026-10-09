
from dotenv import load_dotenv
load_dotenv()

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Search the web for news
search_tool = TavilySearchResults(max_results=5)

# Use Groq instead of Mistral
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)

# Prompt for summarizing news
prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful assistant.

    Summarize the following latest AI news into clear bullet points.
    Include important developments, dates, and source links when available.
    Do not invent facts.

    News:
    {news}
    """
)

# Create the chain
chain = prompt | llm | StrOutputParser()

# Search for AI news
news_result = search_tool.invoke(
    {"query": "Latest AI news of 2026"}
)

# Generate the summary
result = chain.invoke({"news": news_result})

print("\nLatest AI News Summary:\n")
print(result)

# Display tool information
print("\nTool description:", search_tool.description)
print("Tool name:", search_tool.name)
print("Tool arguments:", search_tool.args)