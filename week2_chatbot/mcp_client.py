import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = "https://api.alphaxiv.org/mcp/v1"


class AlphaXivClient:
    def __init__(self):
        self.url = MCP_URL

    async def discover_papers(self, question, keywords=None, difficulty=5):

        if keywords is None:
            keywords = question.split()[:4]

        async with streamablehttp_client(self.url) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:

                await session.initialize()

                return await session.call_tool(
                    "discover_papers",
                    {
                        "question": question,
                        "keywords": keywords,
                        "difficulty": difficulty,
                    },
                )

    async def get_paper_content(self, url: str, full_text: bool = False):

        async with streamablehttp_client(self.url) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:

                await session.initialize()

                return await session.call_tool(
                    "get_paper_content",
                    {
                        "url": url,
                        "fullText": full_text,
                    },
                )


# ----------------------------
# IMPORTANT: sync wrappers
# ----------------------------

_client = AlphaXivClient()


def discover_papers(question, keywords=None, difficulty=5):
    return asyncio.run(
        _client.discover_papers(question, keywords, difficulty)
    )


def get_paper_content(url, full_text=False):
    return asyncio.run(
        _client.get_paper_content(url, full_text)
    )