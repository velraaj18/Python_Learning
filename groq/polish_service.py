from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key= GROQ_API_KEY
)


def polish_transcription(transcript: str) -> str:
    print(transcript)
    """
    Correct multilingual speech-to-text output without translating it.
    """

    prompt = f"""
You are an expert speech-to-text corrector.

The transcript may contain:
- Tamil
- English
- Hindi
- Mixed languages in the same sentence.

Rules:
1. Do NOT translate anything.
2. Preserve every language exactly as spoken.
3. Fix only:
   - spelling mistakes
   - punctuation
   - grammar
   - obvious speech-to-text errors
4. Preserve technical words like:
   API
   JavaScript
   React
   FastAPI
   Python
   Groq
   ChatGPT
5. Return ONLY the corrected transcript.

Transcript:
{transcript}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    print(response.choices[0].message.content.strip())
    return response.choices[0].message.content.strip()