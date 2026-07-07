import os
from agents import Agent, Runner
from config import model
from research_plan import ResearchPlan

planner_agent_instructions = """
    You are a research planner.

    Break the user's topic into 5-8 research questions.
    Do not answer the questions.
"""

planner_agent = Agent(
    name="Planner Agent",
    instructions=planner_agent_instructions,
    model=model,
    output_type=ResearchPlan
)