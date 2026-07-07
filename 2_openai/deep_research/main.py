from planner_agent import planner_agent
from agents import Runner
import asyncio

async def main():
    result = await Runner.run(
        planner_agent,
        "Research AI in Healthcare"
    )
    print(result.final_output)

asyncio.run(main())