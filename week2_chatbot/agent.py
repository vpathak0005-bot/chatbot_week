import os
import json
import asyncio
import requests
import trafilatura

from openai import OpenAI
from dotenv import load_dotenv

from mcp_client import AlphaXivClient

load_dotenv()

# ---------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "nex-agi/nex-n2-pro:free"

# ---------------------------------------------------------------------
# External tools (web)
# ---------------------------------------------------------------------

SERPER_API_KEY = os.environ["SERPER_API_KEY"]

def web_search(query: str) -> dict:
    """Search Google via Serper API."""

    url = "https://google.serper.dev/search"

    res = requests.post(
        url,
        headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        },
        json={"q": query},
        timeout=20,
    )

    data = res.json()

    results = []

    for item in data.get("organic", [])[:5]:
        results.append({
            "title": item.get("title"),
            "link": item.get("link"),
            "snippet": item.get("snippet"),
        })

    return {"results": results}


def web_fetch(url: str) -> dict:
    """Fetch and clean webpage content."""

    try:
        html = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        ).text

        text = trafilatura.extract(html)

        if not text:
            return {"error": "No readable content found"}

        return {
            "url": url,
            "content": text[:12000],
        }

    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------------------
# AlphaXiv MCP client
# ---------------------------------------------------------------------

alpha = AlphaXivClient()

def discover_papers(question: str, keywords=None, difficulty=5):
    return asyncio.run(
        alpha.discover_papers(
            question=question,
            keywords=keywords,
            difficulty=difficulty,
        )
    )


def get_paper_content(url: str, full_text=False):
    return asyncio.run(
        alpha.get_paper_content(
            url=url,
            full_text=full_text,
        )
    )

# ---------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch full content of a webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "discover_papers",
            "description": "Search academic papers from AlphaXiv.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "difficulty": {"type": "integer"},
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_paper_content",
            "description": "Fetch full paper content from AlphaXiv.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "full_text": {"type": "boolean"},
                },
                "required": ["url"],
            },
        },
    },
]

# ---------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------

TOOL_REGISTRY = {
    "web_search": web_search,
    "web_fetch": web_fetch,
    "discover_papers": discover_papers,
    "get_paper_content": get_paper_content,
}

# ---------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------

def dispatch(tool_call):
    """Execute tool safely and return JSON string."""

    try:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments or "{}")

        print(f"[TOOL] {name} -> {args}")

        if name not in TOOL_REGISTRY:
            return json.dumps({"error": "Unknown tool"})

        result = TOOL_REGISTRY[name](**args)

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": str(e)})

# ---------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------

SYSTEM_PROMPT = """
You are a research assistant like Perplexity.

Rules:
- Always search before answering.
- Always use web_fetch if a webpage is provided.
- Use academic papers when relevant.
- Combine sources into a clear answer.
- Cite information from tools.
- If uncertain, say so.
"""

# ---------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------

MAX_ITERATIONS = 8


def run_agent(question: str) -> str:
    """Main ReAct agent loop."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for _ in range(MAX_ITERATIONS):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )

        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # ---------------------------------------------------------
        # Tool execution loop
        # ---------------------------------------------------------
        if finish_reason == "tool_calls":

            messages.append(msg)

            for tool_call in msg.tool_calls:
                result = dispatch(tool_call)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            continue

        # ---------------------------------------------------------
        # Final answer
        # ---------------------------------------------------------
        return msg.content

    return "Failed: max iterations reached"