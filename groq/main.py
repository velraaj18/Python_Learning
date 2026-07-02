from fastapi import FastAPI, UploadFile, File
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI(title="GROQ proxy API")

app.add_middleware(
    CORSMiddleware,
    allow_headers = ["*"],
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_credentials = True
)

client = Groq(
    api_key= GROQ_API_KEY
)

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1]
    print(suffix)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(await file.read())
        temp_path = temp.name

    with open(temp_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo"
        )
        print(transcription)

    os.remove(temp_path)

    return {
        "text": transcription.text
    }
    
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)