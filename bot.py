# important libraries

from dotenv import load_dotenv
import os
import sounddevice as sd
import numpy as np
import io
from pydub import AudioSegment

# Web socket connetion ot the openai api
import asyncio
import websockets
import json



# Load OpenAI API key from .env file

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OpenAI API key is missing. Set it in the .env file.")

# Constants for audio recording
RATE = 24000  # Sample rate (matches OpenAI's expected rate)
CHANNELS = 1  # Mono audio

def record_audio(duration=5):
    print("Recording... Speak now!")
    audio_data = sd.rec(int(duration * RATE), samplerate=RATE, channels=CHANNELS, dtype=np.int16)
    sd.wait()  # Wait until recording is finished
    print("Recording stopped.")
    
    # Convert NumPy array to PCM16 audio bytes
    audio_bytes = audio_data.tobytes()
    
    # Convert to WAV format (optional)
    audio_segment = AudioSegment(
        data=audio_bytes, sample_width=2, frame_rate=RATE, channels=1
    )
    wav_io = io.BytesIO()
    audio_segment.export(wav_io, format="wav")
    return wav_io.getvalue()  # Return WAV data


RATE = 24000  # Sample rate (matches OpenAI's expected rate)
CHANNELS = 1  # Mono audio

# Function to record audio from the microphone

def record_audio(duration=5):
    print("Recording... Speak now!")
    audio_data = sd.rec(int(duration * RATE), samplerate=RATE, channels=CHANNELS, dtype=np.int16)
    sd.wait()  # Wait until recording is finished
    print("Recording stopped.")
    
    # Convert NumPy array to PCM16 audio bytes
    audio_bytes = audio_data.tobytes()
    
    # Convert to WAV format (optional)
    audio_segment = AudioSegment(
        data=audio_bytes, sample_width=2, frame_rate=RATE, channels=1
    )
    wav_io = io.BytesIO()
    audio_segment.export(wav_io, format="wav")
    return wav_io.getvalue()  # Return WAV data


# Function to send audio data to OpenAI's WebSocket API

WS_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-mini-realtime-preview-2024-12-17"

async def send_audio_to_openai(audio_bytes):
    headers = {"Authorization": f"Bearer {API_KEY}", "OpenAI-Beta": "realtime=v1"}

    async with websockets.connect(WS_URL, extra_headers=headers) as ws:
        print("Connected to OpenAI.")

        # Configure session
        session_config = {
            "type": "session.update",
            "session": {
                "instructions": "You are a helpful assistant.",
                "voice": "alloy",
                "temperature": 1,
                "modalities": ["audio", "text"],
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16"
            }
        }
        await ws.send(json.dumps(session_config))
        print("Session configured.")

        # Send recorded audio
        message = {
            "type": "input_audio_buffer.append",
            "audio": audio_bytes.hex()
        }
        await ws.send(json.dumps(message))
        print("Sent audio data.")

        # Process response
        while True:
            response = await ws.recv()
            response_json = json.loads(response)
            print("Received:", response_json)

            if response_json.get("type") == "response.audio.done":
                break  # Stop when audio response is complete

# Function to play audio response from OpenAI

def play_audio(pcm16_bytes):
    audio_segment = AudioSegment(
        data=pcm16_bytes, sample_width=2, frame_rate=RATE, channels=1
    )
    audio_segment.export("response.wav", format="wav")  # Save to file
    print("Playing response...")
    audio_segment.play()


# Main function to record audio, send to OpenAI, and play the response

async def main():
    audio_bytes = record_audio()  # Record user's voice
    await send_audio_to_openai(audio_bytes)  # Send to OpenAI
    play_audio(audio_bytes)  # Play AI response

asyncio.run(main())

