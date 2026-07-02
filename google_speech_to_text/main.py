from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.api_core.client_options import ClientOptions

import asyncio
import threading
import queue
import json
import os

from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
REGION = "us"


# FastAPI
app = FastAPI(title="Google Speech To Text")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "running"}


# Creates Google Speech Client
def create_google_client():
    return SpeechClient(
        client_options=ClientOptions(
            api_endpoint=f"{REGION}-speech.googleapis.com"
        )
    )
    

# Creates Streaming Configuration
def create_streaming_config():
    recognition_config = cloud_speech.RecognitionConfig(
        explicit_decoding_config=
        cloud_speech.ExplicitDecodingConfig(
            encoding= cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            audio_channel_count=1,
        ),
        language_codes=[
            "en-US",
            "ta-IN"
        ],
        model="chirp_3",
    )

    streaming_config = cloud_speech.StreamingRecognitionConfig(
        config=recognition_config,
        streaming_features=
        cloud_speech.StreamingRecognitionFeatures(
            interim_results=True
        )
    )
    
    return cloud_speech.StreamingRecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/{REGION}/recognizers/_",
        streaming_config=streaming_config
    )
    

# Google continuously calls this generator
# asking for the next chunk of audio.
def request_generator(audio_queue: queue.Queue,config_request):

    # First request must always be config.
    yield config_request
    while True:
        chunk = audio_queue.get()
        if chunk is None:
            break
        yield cloud_speech.StreamingRecognizeRequest(
            audio=chunk
        )
        

# Runs inside a background thread.
# Why a thread?

# Google's streaming_recognize() is a blocking API.
# If we run it in FastAPI's event loop, the websocket
# will stop receiving microphone audio.
def google_stream(
    client: SpeechClient,
    websocket: WebSocket,
    websocket_loop,
    audio_queue: queue.Queue,
    config_request,
    session_finished: asyncio.Event
):

    try:
        # Start Google's streaming recognizer.
        responses = client.streaming_recognize(
            requests=request_generator(
                audio_queue,
                config_request
            )
        )
        print("Google stream started")

        # Read responses until Google closes the stream.
        for response in responses:
            
            # Ignore empty responses.
            if not response.results:
                continue
            
            # A single response may contain multiple results.
            for result in response.results:
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript
                print("--------------------------------")
                print("Transcript :", transcript)
                print("Is Final   :", result.is_final)
                print("--------------------------------")
                # Message sent back to browser.
                message = {
                    "type": "transcript",
                    "text": transcript,
                    "is_final": result.is_final
                }

                # We are inside a normal thread.
                # Ask FastAPI's event loop to send the JSON.
                future = asyncio.run_coroutine_threadsafe(
                    websocket.send_json(message),
                    websocket_loop
                )

                # Wait until send_json() finishes.
                # If it throws an exception we'll see it here.
                future.result()

        print("Google stream finished")

        # Tell browser there will be no more transcripts.
        future = asyncio.run_coroutine_threadsafe(
            websocket.send_json({
                "type": "session_complete"
            }),
            websocket_loop
        )
        future.result()

    except Exception as ex:
        print(f"Google Streaming Error: {ex}")

    finally:
        # Notify the websocket coroutine that
        # Google has completely finished.
        websocket_loop.call_soon_threadsafe(
            session_finished.set
        )


# WebSocket Endpoint
@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    # Accept browser connection.
    await websocket.accept()
    print("Browser connected")

    # Save the current asyncio event loop.
    # The Google thread will use this to send messages back to the browser.
    websocket_loop = asyncio.get_running_loop()

    # Queue shared between FastAPI and Google thread.
    audio_queue = queue.Queue()

    # Used to notify FastAPI when Google has completely finished processing.
    session_finished = asyncio.Event()

    # Create Google client.
    client = create_google_client()

    # Create Google configuration request.
    config_request = create_streaming_config()

    # Start Google streaming in a background thread.
    google_thread = threading.Thread(
        target=google_stream,
        args=(
            client,
            websocket,
            websocket_loop,
            audio_queue,
            config_request,
            session_finished,
        ),
        daemon=True,
    )

    google_thread.start()
    
    try:
        while True:
            # Receive either audio bytes or JSON control message.
            message = await websocket.receive()
            
            # Browser sent microphone audio.
            if "bytes" in message:
                audio_queue.put(message["bytes"])
            # Browser sent a control message.
            elif "text" in message:
                control = json.loads(message["text"])
                # User clicked Stop.
                if control.get("type") == "end_of_audio":
                    print("End of audio received.")
                    # Tell Google there is no more audio.
                    audio_queue.put(None)
                    # Don't receive any more websocket messages.
                    break

    except WebSocketDisconnect:
        print("Browser disconnected")
        # Wake up Google if browser disconnects unexpectedly.
        audio_queue.put(None)

    finally:
        print("Waiting for Google to finish...")
        # Wait until Google has flushed all transcripts.
        await session_finished.wait()
        # Ensure background thread exits cleanly.
        google_thread.join()
        print("Closing websocket")
        await websocket.close()
        print("Connection closed")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)