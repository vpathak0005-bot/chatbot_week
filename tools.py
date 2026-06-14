import os
import requests

SERPER_API_KEY = os.environ["SERPER_API_KEY"]

def web_search(query: str) -> dict:
    url = "https://google.serper.dev/search"

    response = requests.post(
        url,
        headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        },
        json={"q": query},
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("organic", [])[:5]:
        results.append(
            {
                "title": item["title"],
                "link": item["link"],
                "snippet": item["snippet"],
            }
        )

    return {"results": results}

import requests
import trafilatura

def web_fetch(url: str) -> dict:
    html = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    ).text

    text = trafilatura.extract(html)

    if not text:
        return {"error": "No readable content found"}

    return {
        "url": url,
        "content": text[:12000]
    }