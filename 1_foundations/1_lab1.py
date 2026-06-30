#Open AI is a light weight python library for HTTP requests for LLMs.
from openai import OpenAI

# OpenAI, deepseek, GROC, Anthropic models all can be called using this OpenAI() function (may be different params)
ollama_base_url = "http://localhost:11434/v1"
ollama = OpenAI(base_url= ollama_base_url, api_key="ollama")

messages = [{"role" : "user", "content" : "What is 2+2?"}]

# To create a chat with the LLM
response = ollama.chat.completions.create(model="llama3.2", messages=messages)

#Complete Response
# ChatCompletion(id='chatcmpl-332', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='2 + 2 = 4.', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=None))], created=1782792971, model='llama3.2', object='chat.completion', moderation=None, service_tier=None, system_fingerprint='fp_ollama', usage=CompletionUsage(completion_tokens=9, prompt_tokens=32, total_tokens=41, completion_tokens_details=None, prompt_tokens_details=None))

# Traverse through the dictionary to get the answer for the question
answer = response.choices[0].message.content

print(answer)