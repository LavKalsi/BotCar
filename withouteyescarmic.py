# pi_assistant_espeak_parallel.py
# Raspberry Pi AI Car Assistant — wake word + commands + vision + espeak (asynchronous feedback)
# Compatible with Raspberry Pi 5 (Python 3.11+)

import speech_recognition as sr
import sounddevice as sd
import numpy as np
import io
import scipy.io.wavfile as wav
import subprocess
import cv2
import base64
import os
from threading import Thread
from openai import OpenAI

# ---------------- CONFIG ----------------
SAMPLE_RATE = 16000
WAKE_WORDS = ["hello", "hey", "computer", "buddy", "hi", "smart mirror"]
VISION_COMMANDS = [
    "what can you see",
    "what is in front of you",
    "what are you looking at",
    "describe the scene",
    "describe what you see",
]

# Initialize OpenAI client
client = OpenAI(api_key="")  # <-- Replace with your key

# Initialize recognizer
recognizer = sr.Recognizer()

# ---------------- UTILS ----------------
def speak(text):
    """Speak text asynchronously using espeak."""
    if not text:
        return
    print(f"[SPEAK] {text}")
    # Run espeak in background so it doesn't block
    subprocess.Popen(["espeak", "-v", "en-us", "-s", "200", text])

def record_audio(duration):
    """Record audio from mic for the given duration (seconds)."""
    print(f"? Recording for {duration} seconds...")
    audio = sd.rec(int(SAMPLE_RATE * duration), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    return np.squeeze(audio)

def audio_data_from_numpy(np_audio):
    """Convert numpy array to AudioFile for SpeechRecognition."""
    byte_io = io.BytesIO()
    wav.write(byte_io, SAMPLE_RATE, np_audio)
    byte_io.seek(0)
    return sr.AudioFile(byte_io)

def listen(duration=4):
    """Record and transcribe speech using Google STT."""
    np_audio = record_audio(duration)
    with audio_data_from_numpy(np_audio) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio).lower()
        return text
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print("Recognition Error:", e)
        return ""

# ---------------- CAMERA ----------------
def capture_image(filename="/tmp/pi_image.jpg"):
    """Capture an image from the Pi camera or USB webcam."""
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to capture image")
        return None
    cv2.imwrite(filename, frame)
    print(f"Image saved to {filename}")
    return filename

# ---------------- OPENAI ----------------
def ask_openai(question):
    """Call GPT-3.5-Turbo (text-only) for conversation."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly AI car assistant."},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI API Error:", e)
        return "Sorry, I couldn't get a response from the AI."

def analyze_image_with_openai(image_path):
    """Analyze image with GPT-4o-mini multimodal model."""
    try:
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that describes what the car's camera sees. "
                        "Focus on the main object in front, or give a one-line environment description if no main object."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe clearly what is visible in this image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                    ]
                }
            ],
            max_tokens=200,
        )

        description = response.choices[0].message.content.strip()

        # Delete image to save space
        try:
            os.remove(image_path)
            print(f"Deleted {image_path} to save space.")
        except Exception as e:
            print("Warning: could not delete image:", e)

        return description

    except Exception as e:
        print("OpenAI image analysis error:", e)
        return "Sorry, I couldn't analyze the image."

# ---------------- MAIN LOOP ----------------
print("🚗 Pi Assistant started. Say a wake word...")

while True:
    # Step 1: listen for wake word
    text = listen(duration=2)
    print("Heard:", text)

    if any(wake_word in text for wake_word in WAKE_WORDS):
        print("Wake word detected!")

        # Step 2: speak Yes? in a separate thread so listening can start immediately
        feedback_thread = Thread(target=speak, args=("Yes?",))
        feedback_thread.start()

        # Step 3: listen for the actual command while espeak is speaking
        command_text = listen(duration=6)
        print("Command heard:", command_text)

        # Step 4: check for vision-related commands
        if any(cmd in command_text for cmd in VISION_COMMANDS):
            img_path = capture_image()
            if img_path:
                reply = analyze_image_with_openai(img_path)
                print("? Bot:", reply)
                speak(reply)
            continue

        # Step 5: other conversation flow
        if command_text:
            reply = ask_openai(command_text)
            print("? Bot:", reply)
            speak(reply)
