from crewai import Agent, Task, Process, Crew
from crewai.project import agent, task, crew, CrewBase
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import List

# Structured output for the task using Pydantic classes

class TrendingCompany(BaseModel):
    """ A company that is in the news and attracting attention """
    name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    reason: str = Field(description="Reason this company is trending in the news")

class TrendingCompanyList(BaseModel):
    """ List of multiple trending companies that are in the news """
    companies: List[TrendingCompany] = Field(description="List of companies trending in the news")
    
@CrewBase
class StockPicker():
    """ Stock Picker Crew """
    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def trending_company_finder(self) -> Agent:
        print(self.agents_config)
        print(self.agents_config.keys())
        return Agent(
            config = self.agents_config['trending_company_finder'],
            verbose = True,
            tools= [SerperDevTool()] #Search tool provided by google
        )
        
    @agent
    def best_company_finder(self) -> Agent:
        print(self.agents_config)
        print(self.agents_config.keys())
        return Agent(
            config = self.agents_config['best_company_finder'],
            verbose = True
        )
        
    @task
    def find_trending_companies(self) -> Task:
        return Task(
            config= self.tasks_config['find_trending_companies'],
            verbose = True,
            output_pydantic= TrendingCompanyList
        )
        
    @task
    def find_best_company(self) -> Task:
        return Task(
            config= self.tasks_config['find_best_company'],
            verbose = True
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents= self.agents,
            tasks= self.tasks,
            process= Process.sequential,
            verbose= True
        )