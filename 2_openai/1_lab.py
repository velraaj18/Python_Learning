from dotenv import load_dotenv
from agents import Agent, Runner, trace
from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
import os

load_dotenv(override=True)

# Configure the GROQ client to use open AI SDK agent
client = AsyncOpenAI(
    api_key= os.getenv("GROQ_API_KEY"),
    base_url= "https://api.groq.com/openai/v1"
)

model = OpenAIChatCompletionsModel(
    model="llama-3.1-8b-instant",
    openai_client=client
)

# Create an instance of the openai SDK agent
# Even though it is openai SDK agent we can use LLM models other than Open AI
agent = Agent(name="Joke teller", instructions="You are a joke teller", model=model)

# Call runner.run method to run the agent
with trace("Telling a joke"):
    result = Runner.run_sync(agent, "Tell a joke about MS dhoni")
    print(result)

