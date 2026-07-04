from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def transcribe_with_groq(audio_file_path: str) -> str:
    """
    Use Groq's audio transcription with explicit multilingual support.
    """
    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            # Critical: Don't force language detection - let it auto-detect
            # This helps with code-switching (Tanglish/mixed content)
            # prompt="""
            # The speaker may switch naturally between Tamil, English, Hindi, and Tanglish.

            # This is conversational speech.
            # The transcript below contains:
            # - Tamil (தமிழ்)
            # - English
            # - Hindi (हिन्दी)
            # - Tanglish (Tamil words written in English script)
            # - Mixed code-switching

            # YOUR TASK:
            # 2. DO NOT translate anything - preserve all languages exactly as spoken

            # 3. For Tanglish:
            # - Correct phonetic English spelling to proper Tamil transliteration
            # - Example: "edhir" → "edhir" (if that's how it sounds), keep natural
            # - Don't convert to Tamil script - keep Tanglish as is
            # """,
            temperature= 0
        )
    print(transcription.text)
    return transcription.text


def polish_transcription(transcript: str) -> str:
    """
    Post-process transcription using Groq's LLM for multilingual correction.
    Handles Tamil, English, Hindi, and Tanglish (code-switching).
    """
    print(f"Raw transcript: {transcript}")
    
    prompt = f"""You are an expert multilingual speech-to-text corrector specializing in Indian languages.

The transcript below contains:
- Tamil (தமிழ்)
- English
- Hindi (हिन्दी)
- Tanglish (Tamil words written in English script)
- Mixed code-switching

YOUR TASK:
1. Fix ONLY genuine transcription errors:
   - Spelling mistakes
   - Punctuation
   - Grammar
   - Obvious Whisper misheard words

2. Strictly no translation - preserve all languages exactly as spoken

3. For Tanglish:
   - Correct phonetic English spelling to proper Tamil transliteration
   - Example: "edhir" → "edhir" (if that's how it sounds), keep natural
   - Don't convert to Tamil script - keep Tanglish as is

4. Preserve technical terms:
   API, JavaScript, React, FastAPI, Python, Groq, ChatGPT, GitHub, etc.

5. Add proper Tamil punctuation where needed (், ?, !):
   - Tamil comma: ،
   - Tamil full stop: ۔
   - But respect English punctuation in English sentences

6. When there's code-switching (Tamil-English mix in same sentence):
   - Keep both languages
   - Fix only language-specific errors
   - Don't force one language

OUTPUT: Return ONLY the corrected transcript, nothing else.

Transcript to correct:
{transcript}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2  # Slightly higher than 0 for better multilingual handling
    )
    
    corrected = response.choices[0].message.content.strip()
    print(f"Corrected transcript: {corrected}")
    return corrected


def transcribe_and_polish(audio_file_path: str) -> str:
    """
    End-to-end transcription pipeline for multilingual audio.
    """
    raw_transcript = transcribe_with_groq(audio_file_path)
    # polished_transcript = polish_transcription(raw_transcript)
    return raw_transcript