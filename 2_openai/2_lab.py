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
    model="llama-3.1-8b-instant",
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

if __name__ == "__main__":
    asyncio.run(pick_and_send_email())