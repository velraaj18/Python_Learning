from pydantic import BaseModel, Field

class FinalReport(BaseModel):
    title: str = Field(description="Title of the research report")
    report: str = Field(description="The complete research report in Markdown format")