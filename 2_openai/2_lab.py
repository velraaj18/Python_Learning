from agents import Agent, Runner, trace, function_tool
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
import os
import asyncio
import resend

load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

model = OpenAIChatCompletionsModel(
    model="openai/gpt-oss-20b",
    openai_client= client
)

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

# Function to run 3 agents in parallel
async def parallel_agents():
    message = "Write a cold sales email"

    with trace("Running 3 agents in parallel"):
        results = await asyncio.gather(
            Runner.run(sales_agent1, message),
            Runner.run(sales_agent2, message),
            Runner.run(sales_agent3, message),
        )
    
    for result in results:
        print(result.final_output)
        print("-" * 80)
        

        
# Tools
# Converting the agents into tools

tool1 = sales_agent1.as_tool(tool_name= "tool_1", tool_description="Professional Sales Agent")        
tool2 = sales_agent2.as_tool(tool_name= "tool_2", tool_description="Engaging Sales Agent")        
tool3 = sales_agent3.as_tool(tool_name= "tool_3", tool_description="Busy Sales Agent")        

# Converting functions into tools using keyword @function_tool
# function to select the best sales email from the 3 agents
@function_tool
async def sales_picker():
    sales_picker = Agent(
    name="sales_picker",
    instructions="You pick the best cold sales email from the given options. \
        Imagine you are a customer and pick the one you are most likely to respond to. \
        Do not give an explanation; reply with the selected email only.",
    model=model
    )
    
    message = "Write a cold sales email"

    with trace("Sales Picker Agent"):
        results = await asyncio.gather(
            Runner.run(sales_agent1, message),
            Runner.run(sales_agent2, message),
            Runner.run(sales_agent3, message),          
        )
        outputs = [result.final_output for result in results]
        emails = "Cold sales emails:\n\n" + "\n\nEmail:\n\n".join(outputs)
        
        best_email = await Runner.run(sales_picker, emails)
        print(best_email.final_output)    
        return best_email.final_output

    
tools = [tool1, tool2, tool3]
#print(tools)

async def send_email(
    content: str,
) -> str:
    """Send out an email with the given subject and content to all sales prospects using Resend"""

    resend.api_key = RESEND_API_KEY

    result = resend.Emails.send({
        "from": "onboarding@resend.dev",   # or your verified domain
        "to": ["velraaj30@gmail.com"],
        "subject": "best email",
        "html": content,
    })

    return f"Email sent successfully. ID: {result['id']}"

# planning and send the email
async def pick_and_send_email():
    instructions = """
        You have exactly three tools.

        You MUST call:
        - tool_1 exactly once
        - tool_2 exactly once
        - tool_3 exactly once

        After you have called all three tools, you already have all the information you need.

        DO NOT call any tool again.

        DO NOT repeat tool calls.

        DO NOT ask for more drafts.

        Immediately compare the three drafts and return the single best email.
        
        """
    
    agent = Agent(name = "Sales_manager", instructions=instructions, tools=tools, model=model)
    
    with trace("Sales manager"):
        result = await Runner.run(agent, "Send a cold sales email addressed to 'Dear CEO'")
        print(result.final_output)
        
    email = result.final_output

    if "Subject:" not in email:
        raise ValueError("Manager did not return an email.")

    await send_email(email)
    
# Email Manager Setup
subject_instructions = "You write compelling subject lines for cold sales emails that get high open rates."
html_instructions = "Convert a text email body to a professional HTML email body with clear formatting."

subject_writer = Agent(name="Subject Writer", instructions=subject_instructions, model=model)
subject_tool = subject_writer.as_tool(tool_name="subject_writer", tool_description="Write a subject for a cold sales email")

html_converter = Agent(name="HTML Converter", instructions=html_instructions, model=model)
html_tool = html_converter.as_tool(tool_name="html_converter", tool_description="Convert a text email body to an HTML email body")

@function_tool
def send_html_email(subject: str, html_body: str) -> str:
    """Send out an email with the given subject and HTML body to all sales prospects"""
    resend.api_key = RESEND_API_KEY
    result = resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": ["velraaj30@gmail.com"],
        "subject": subject,
        "html": html_body,
    })
    return f"Email sent successfully. ID: {result['id']}"

email_manager_instructions = """You are an email formatter and sender. You receive the body of an email to be sent.

Follow these steps:
1. Use the subject_writer tool to write a subject for the email
2. Use the html_converter tool to convert the body to HTML
3. Use the send_html_email tool to send the email with the subject and HTML body"""

email_manager = Agent(
    name="Email Manager",
    instructions=email_manager_instructions,
    tools=[subject_tool, html_tool, send_html_email],
    model=model,
    handoff_description="Convert an email to HTML and send it"
)

# Sales Manager Setup
sales_manager_instructions = """You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email.

Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools (tool_1, tool_2, tool_3) to generate three different email drafts. Call each tool exactly once.

2. Evaluate and Select: Review the three drafts and choose the single best email using your judgment of which one is most effective.

3. Handoff for Sending: Pass ONLY the winning email draft to the 'Email Manager' agent. The Email Manager will take care of formatting and sending.

Important Rules:
- You must call tool_1, tool_2, and tool_3 exactly once each
- Do not call any tool more than once
- After getting all three drafts, immediately select the best one
- Hand off exactly ONE email to the Email Manager — never more than one"""

sales_manager = Agent(
    name="Sales Manager",
    instructions=sales_manager_instructions,
    tools=[tool1, tool2, tool3],
    handoffs=[email_manager],
    model=model
)

async def sales_manager_workflow():
    message = "Send out a cold sales email addressed to Dear CEO from Alice"
    
    with trace("Automated SDR"):
        result = await Runner.run(sales_manager, message)
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(sales_manager_workflow())