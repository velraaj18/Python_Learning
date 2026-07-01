from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import asyncio
import json

load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(GEMINI_API_KEY)

app = FastAPI(title="Gemini proxy API")

#Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_headers = ["*"],
    allow_credentials = True,
    allow_methods = ["*"]
)

#Initialize GenAI client
genai_client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-3.1-flash-live-preview"

@app.get("/healthCheck")
async def health_check():
    return {"message" : "Connected"}

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "type": "status",
            "message": "🟢 Ready to transcribe",
            "status": "connected"
        })
        
        audio_chunks = []
        
        async def collect_audio():
            """Collect audio chunks from browser until stop signal"""
            try:
                while True:
                    message = await websocket.receive()
                    
                    if "bytes" in message:
                        data = message["bytes"]
                        if data:
                            audio_chunks.append(data)
                    
                    elif "text" in message:
                        control = json.loads(message["text"])
                        if control.get("action") == "stop":
                            break
            
            except WebSocketDisconnect:
                pass
            except Exception as e:
                print(f"Error collecting audio: {e}")
        
        async def transcribe_audio():
            """Transcribe audio after collection stops"""
            await collect_audio()
            
            if audio_chunks:
                combined_audio = b''.join(audio_chunks)
                
                try:
                    response = await asyncio.to_thread(
                        genai_client.models.transcribe_audio,
                        model=MODEL,
                        audio=types.Blob(
                            data=combined_audio,
                            mime_type="audio/pcm"
                        )
                    )
                    
                    await websocket.send_json({
                        "type": "transcript",
                        "role": "user",
                        "text": response.text
                    })
                    print(f"Transcription: {response.text}")
                
                except Exception as e:
                    print(f"Transcription error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Transcription error: {e}"
                    })
        
        await transcribe_audio()
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Connection error: {e}"
        })