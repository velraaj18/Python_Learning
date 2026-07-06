from dotenv import load_dotenv
from agents import Agent, Runner, trace, OpenAIChatCompletionsModel, function_tool, GuardrailFunctionOutput, input_guardrail, InputGuardrailTripwireTriggered
import os
import asyncio
from openai import AsyncOpenAI
from pydantic import BaseModel
import resend

load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

model = OpenAIChatCompletionsModel(model="openai/gpt-oss-20b", openai_client=client)

# Giving the set of instructions
instructions1 = "You are a sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write professional, serious cold emails."

instructions2 = "You are a humorous, engaging sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write witty, engaging cold emails that are likely to get a response."

instructions3 = "You are a busy sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write concise, to the point cold emails."

sales_agent1 = Agent(
        name="Professional Sales Agent",
        instructions=instructions1,
        model=model
)

sales_agent2 = Agent(
        name="Engaging Sales Agent",
        instructions=instructions2,
        model=model
)

sales_agent3 = Agent(
        name="Busy Sales Agent",
        instructions=instructions3,
        model=model
)

# Tools
# Converting the agents into tools

description = "Write a cold sales email"

tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description)
tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=description)
tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description=description)

@function_tool
def send_html_email(subject: str, html_body: str) -> dict[str, str]:
    """Send out an email with the given subject and content to all sales prospects using Resend"""

    resend.api_key = RESEND_API_KEY

    result = resend.Emails.send({
        "from": "onboarding@resend.dev",   # or your verified domain
        "to": ["velraaj30@gmail.com"],
        "subject": subject,
        "html": html_body,
    })
    
    return {"status": "success"}    

subject_instructions = "You can write a subject for a cold sales email. \
You are given a message and you need to write a subject for an email that is likely to get a response."

html_instructions = "You can convert a text email body to an HTML email body. \
You are given a text email body which might have some markdown \
and you need to convert it to an HTML email body with simple, clear, compelling layout and design."

subject_writer = Agent(name="Email subject writer", instructions=subject_instructions, model=model)
subject_tool = subject_writer.as_tool(tool_name="subject_writer", tool_description="Write a subject for a cold sales email")

html_converter = Agent(name="HTML email body converter", instructions=html_instructions, model=model)
html_tool = html_converter.as_tool(tool_name="html_converter",tool_description="Convert a text email body to an HTML email body")

email_tools = [subject_tool, html_tool, send_html_email]

instructions ="You are an email formatter and sender. You receive the body of an email to be sent. \
You first use the subject_writer tool to write a subject for the email, then use the html_converter tool to convert the body to HTML. \
Finally, you use the send_html_email tool to send the email with the subject and HTML body."


emailer_agent = Agent(
    name="Email Manager",
    instructions=instructions,
    tools=email_tools,
    model=model
)

email_manager_tool = emailer_agent.as_tool(tool_name= "email_manager_tool", tool_description="Convert an email to HTML and send it")
tools = [tool1, tool2, tool3, email_manager_tool]
sales_manager_instructions = """
    You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.
    
    Follow these steps carefully:
    1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. Do not proceed until all three drafts are ready.
    2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
    You can use the tools multiple times if you're not satisfied with the results from the first try.
    3. Handoff for Sending: Pass ONLY the winning email draft to the 'Email Manager' agent. The Email Manager will take care of formatting and sending.
    
    Crucial Rules:
    - You must use the sales agent tools to generate the drafts — do not write them yourself.
    - You must hand off exactly ONE email to the Email Manager — never more than one.
    """
    
async def sales_manager():
    sales_manager = Agent(
        name="Sales Manager",
        instructions=sales_manager_instructions,
        tools=tools,
        model=model)

    message = "Send out a cold sales email addressed to Dear CEO from Alice"

    with trace("Automated SDR"):
        result = await Runner.run(sales_manager, message)
        print(result)
        
class NameCheckOutput(BaseModel):
    is_name_in_message: bool
    name: str | None = None
    
guardrail_agent = Agent(
    name= "Name check",
    instructions="Check if the user is including someone's personal name in what they want you to do.",
    output_type= NameCheckOutput,
    model= model
)
    
@input_guardrail
async def guardrail_against_name(ctx, agent, message):
    result = await Runner.run(guardrail_agent, message, context=ctx.context)
    print(result.final_output)
    is_name_in_message = result.final_output.is_name_in_message
    return GuardrailFunctionOutput(output_info={"found_name": result.final_output},tripwire_triggered=is_name_in_message)

async def careful_sales_manager():
    careful_sales_manager = Agent(
        name= "Sales Manager",
        instructions= sales_manager_instructions,
        tools= tools,
        input_guardrails= [guardrail_against_name],
        model=model
    )
    
    message = "Send out a cold sales email addressed to Dear CEO from Alice"

    try:
        with trace("Protected Automated SDR"):
            result = await Runner.run(careful_sales_manager, message)
            print(result.final_output)

    except InputGuardrailTripwireTriggered as e:
        print("❌ Guardrail blocked the request.")
        print(e)

if __name__ == "__main__":
    asyncio.run(careful_sales_manager())