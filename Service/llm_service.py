import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# LangChain-compatible LLM for LangGraph
langgraph_llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="qwen/qwen3-32b",  # qwen/qwen3-32b gemma2-9b-it
    temperature=0.4,
)
