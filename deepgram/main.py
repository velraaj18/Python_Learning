from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import websockets
import asyncio
import os
from dotenv import load_dotenv


# Load the API key from the .env file
load_dotenv()

app = FastAPI(title= "Deepgram Proxy API")

# Allow our front end to connect [CORS Policy]
app.add_middleware(
    CORSMiddleware,
    allow_origins =["*"],
    allow_headers = ["*"],
    allow_credentials = True,
    allow_methods = ["*"]
)

# Get the API key from the .env file
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
print(DEEPGRAM_API_KEY)

@app.get("/health")
async def health_check():
    return{"message" : "connected"}

@app.websocket("/ws/transcribe")
async def websocket_transcribe(client_socket : WebSocket):
    ''' API to get the audio samples from the client 
        and send it to the deepgram and send transcripts
        back to the client
    '''
    
    # First accept the websocket from the client
    await client_socket.accept()

    try:
        #Connect to deepgram
        deepgram_uri = (
            "wss://api.deepgram.com/v1/listen?"
            "encoding=linear16&sample_rate=16000&channels=1"
            "&interim_results=true&model=nova-3"
        )

        # Create WebSocket with authentication header
        async with websockets.connect(
            deepgram_uri,
            subprotocols=["token", DEEPGRAM_API_KEY],
        ) as deepgram_socket:
            # Create two concurrent tasks:
            # 1. Listen to browser and send to Deepgram
            # 2. Listen to Deepgram and send to browser
             await asyncio.gather(
                client_to_deepgram(client_socket, deepgram_socket),
                deepgram_to_client(deepgram_socket, client_socket)
            )
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        await client_socket.close(code=1000)

async def client_to_deepgram(client_socket : WebSocket, deepgram_ws):
    ''' Listen to the audio from the client socket
        And send it to deepgram web socket '''
    try:
        while True:
            data = await client_socket.receive_bytes()
            await deepgram_ws.send(data)
    except Exception as e:
        print(f"Client to Deepgram relay error: {e}")
        
async def deepgram_to_client(deepgram_ws, client_socket: WebSocket):
    '''Recieve message from deepgram and send it to the client'''
    try:
       async for message in deepgram_ws:
           await client_socket.send_text(message)
    except Exception as e:
        print(f"Deepgram to client relay error: {e}")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


