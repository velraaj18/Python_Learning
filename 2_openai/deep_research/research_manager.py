from research_plan import ResearchPlan
from research_result import  ResearchResult
from final_report import FinalReport
from planner_agent import planner_agent
from research_agent import research_agent
from writer_agent import writer_agent
from config import model

from agents import Agent, Runner, trace
from typing import List
import asyncio

class ResearchManager:
    async def plan_research(self, query: str) -> ResearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(planner_agent, input=query)
        return result.final_output_as(ResearchPlan)
        
    async def perform_research(self, plan: ResearchPlan) -> List[str]:
        """ Perform Research for the planned topics and questions """
        print("Performing Research...")
        tasks = []

        for item in plan.research_items:
            for question in item.questions:
                tasks.append(
                    Runner.run(research_agent, question)
                )

        results = await asyncio.gather(*tasks)

        research_results = [
            result.final_output_as(str)
            for result in results
        ]
        
        return research_results
    
    async def write_report(self, query:str, research_results: List[str]) -> FinalReport:
        """ Write the report for the query """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {research_results}"
        result = await Runner.run(writer_agent, input)
        return result.final_output_as(FinalReport)
            
    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        with trace("Research Manager"):
            print("Starting research...")
            research_plan = await self.plan_research(query)
            yield "Searches planned, starting to search..." 
            research_results = await self.perform_research(research_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, research_results)
            yield "Report written, Research Complete"
            yield report.report