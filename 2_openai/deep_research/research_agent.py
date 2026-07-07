from agents import Agent, function_tool
from config import model
from research_result import ResearchResult
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@function_tool
def search_web(query: str) -> str:
    """
    Search the web and return the findings.
    """

    response = client.chat.completions.create(
        model="groq/compound",
        messages=[
            {
                "role": "user",
                "content": query
            }
        ]
    )

    message = response.choices[0].message

    result = f"Summary:\n{message.content}\n\n"

    if message.executed_tools:
        result += "Sources:\n"

        for tool in message.executed_tools:
            if tool.search_results:
                for source in tool.search_results:
                    result += (
                        f"Title: {source.title}\n"
                        f"URL: {source.url}\n\n"
                    )

    return result

research_agent = Agent(
    name="Research Agent",
    model=model,
    tools=[search_web],
    output_type=ResearchResult,
    instructions="""
You are a professional research assistant.

When given a research question:

1. Call the search_web tool.
2. Use ONLY the information returned by the tool.
3. Produce a concise summary.
4. Populate the ResearchResult schema.

The output MUST contain:

- question
- summary
- sources

For each source include:
- title
- url

Do not invent sources.
"""
)