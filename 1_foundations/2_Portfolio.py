import os
from dotenv import load_dotenv
from pypdf import PdfReader
import gradio as gr
import requests
import json
from groq import Groq

load_dotenv(override=True)

#Groq api key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

#Push over
PUSH_OVER_APPLICATION_KEY = os.getenv("PUSH_OVER_APPLICATION_KEY")
PUSH_OVER_USER_KEY = os.getenv("PUSH_OVER_USER_KEY")
PUSH_OVER_URL = "https://api.pushover.net/1/messages.json"

if(PUSH_OVER_APPLICATION_KEY):
    print("push over application token found")
else:
    print("Push over application token not found")
    
if(PUSH_OVER_USER_KEY):
    print("Push over user found")
else:
    print("Push over user not found")

#Function to send push notification using "POST" API    
def push(text):
    requests.post(
        url= PUSH_OVER_URL,
        data={
            "token" : PUSH_OVER_APPLICATION_KEY,
            "user" : PUSH_OVER_USER_KEY,
            "message" : text
        }
    )

#Test case
#push("Hello")

# Function to record the user details who wants to get in touch
def record_user_details(email, name="Name not provided", notes="Additional Notes"):
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return{
        "recorded": "ok"
    }

# Function to record the unknown questions asked by the user
def record_unknown_questions(question):
    push(f"Recording {question} asked that I couldn't answer")
    return{
        "recorded" : "ok"
    }
    
# Tool creation using plain json

record_user_details_json = {
    "name" : "record_user_details",
    "description":"Call this tool ONLY after the user has explicitly provided their email address. Never guess or invent an email address. Do not call this tool before an email is provided.",
    "parameters" : {
        "type" : "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_questions_json = {
    "name": "record_unknown_questions",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{
    "type" : "function", "function" : record_user_details_json
}, {
    "type" : "function", "function" : record_unknown_questions_json
}]

# print(tools)

# Create a new class
class Me:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.name = "Velraaj"
        self.linkedin = ""
        
        #Read the contents of the linkedin PDF using pypdf package -> PdfReader method
        reader = PdfReader("me/Linkedin.pdf")
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        #Read the content from the summary text file
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    # Fucntion to handle the tools from the AI response for the user question if any tool needed
    def handle_tool_call(self, tool_calls):
        print(tool_calls)
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            
            if tool_name == "record_user_details":
                result = record_user_details(**arguments)
            elif tool_name == "record_unknown_questions":
                result = record_unknown_questions(**arguments)
            
            results.append({"role" : "tool", "content" : json.dumps(result), "tool_call_id" : tool_call.id })

        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
                        particularly questions related to {self.name}'s career, background, skills and experience. \
                        Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
                        You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
                        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
                        If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
                        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self,message,history):
        print(history)
        clean_history = []

        for msg in history:
            clean_history.append({
                "role": msg["role"],
                "content": msg["content"][0]["text"]
            })
            
        messages = [{"role" : "system", "content" : self.system_prompt()}] + clean_history + [{"role" : "user", "content" : message}]
        done = False
        while not done:
            response = self.client.chat.completions.create(model="llama-3.1-8b-instant", messages= messages, tools=tools)
            print(response)
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
                
        return response.choices[0].message.content


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat).launch()