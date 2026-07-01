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
async def websocket_transcribe(websocket : WebSocket):
    await websocket.accept()
    
    gemini_session = None
    recording_active = True 
    
    try:
        # Configure Gemini Live API
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],  # Changed from TEXT to AUDIO
            input_audio_transcription=types.AudioTranscriptionConfig(),
            temperature=0.7,
            max_output_tokens=256,
        )
        # Connect to Gemini Live API
        async with genai_client.aio.live.connect(model=MODEL, config=config) as gemini_session:
            
            print("✅ Connected to Gemini Live API")
            await websocket.send_json({
                "type": "status",
                "message": "🟢 Connected to Gemini",
                "status": "connected"
            })
            async def forward_audio():
                """Forward browser audio to Gemini"""
                nonlocal recording_active  # Access the outer flag
                try:
                    while recording_active:
                        # Receive either binary audio data or JSON control message
                        message = await websocket.receive()
                        
                        if "bytes" in message:
                            data = message["bytes"]
                            if data and recording_active:
                                await gemini_session.send_realtime_input(
                                    audio=types.Blob(
                                        data=data,
                                        mime_type="audio/pcm"
                                    )
                                )
                        elif "text" in message:
                            # Handle control messages
                            control = json.loads(message["text"]) 
                            if control.get("action") == "stop":
                                recording_active = False
                                break
                            
                except WebSocketDisconnect:
                    print("Browser disconnected")
                    recording_active = False
                except Exception as e:
                    print(f"Audio forward error: {e}")
                    recording_active = False
            
            async def handle_gemini_responses():
                """Handle Gemini responses and send to browser"""
                nonlocal recording_active
                try:
                    async for response in gemini_session.receive():
                        if not response.server_content:
                            continue
                        
                        # Input transcription (what user said)
                        if response.server_content.input_transcription:
                            transcript = response.server_content.input_transcription.text
                            if transcript:  # ✅ Only send if text exists
                                await websocket.send_json({
                                    "type": "transcript",
                                    "role": "user",
                                    "text": transcript
                                })
                                print(f"Input Transcription: {transcript}")
                        
                        # Model response (text) - FIXED
                        if response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                # ✅ Check if part has text AND it's not null
                                if hasattr(part, 'text') and part.text:
                                    await websocket.send_json({
                                        "type": "response",
                                        "role": "assistant",
                                        "text": part.text
                                    })
                                    print(f"model response: {part.text}")
                        
                        # Output transcription (what model said) - PREFERRED for text
                        if response.server_content.output_transcription:
                            transcript = response.server_content.output_transcription.text
                            if transcript:  # ✅ Only send if text exists
                                await websocket.send_json({
                                    "type": "transcript",
                                    "role": "assistant",
                                    "text": transcript
                                })
                                print(f"output Transcription: {transcript}")
                        
                        # ✅ Send turn_complete signal to frontend
                        if response.server_content.turn_complete and recording_active:
                            await websocket.send_json({
                                "type": "turn_complete",
                                "role": "assistant"
                            })
                        elif not recording_active:
                            break # Exit the loop if recording stopped
                
                except Exception as e:
                    print(f"Response handler error: {e}")
                    await websocket.send_json({"type": "error", "message": str(e)})
            
            # Run both tasks concurrently
            await asyncio.gather(
                forward_audio(),
                handle_gemini_responses()
            )
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Connection error: {e}"
        })
    
    finally:
        if gemini_session:
            await gemini_session.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)