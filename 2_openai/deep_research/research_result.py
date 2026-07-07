from pydantic import BaseModel, Field
from typing import List


class Source(BaseModel):
    title: str = Field(description="Title of the source")
    url: str = Field(description="URL of the source")


class ResearchResult(BaseModel):
    question: str = Field(description="Research question")
    summary: str = Field(description="Summary of the findings")
    sources: List[Source] = Field(description="Sources used")