from pydantic import BaseModel, Field
from typing import List

class FinalReport(BaseModel):
    title: str = Field(description="Title of the research report")
    report: List[str] = Field(description="The complete research report in Markdown format")