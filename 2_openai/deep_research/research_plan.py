from pydantic import BaseModel, Field
from typing import List

class ResearchItem(BaseModel):
    topic : str = Field(description="This field holds the topic for the Research Item")
    questions : List[str] = Field(description="This field holds the list of questions related to the topic of the research Item")
    
class ResearchPlan(BaseModel):
    research_items : List[ResearchItem] = Field(description="A list of web searches to perform to best answer the topic.")