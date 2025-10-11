# carmic.py
# Pi Car Assistant with voice, vision, and interactive eyes
# Works with Raspberry Pi 5, Python 3.11+

import threading
import time
import os
import cv2
import base64
import subprocess
import numpy as np
import io
import scipy.io.wavfile as wav
import speech_recognition as sr
from openai import OpenAI
import sounddevice as sd
import pygame
from car_eyes import focus_center, show_image  # import the functions from car_eyes.py

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
    subprocess.Popen(["espeak", "-v", "en-us", "-s", "200", text])

def record_audio(duration):
    audio = sd.rec(int(SAMPLE_RATE * duration), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    return np.squeeze(audio)

def audio_data_from_numpy(np_audio):
    byte_io = io.BytesIO()
    wav.write(byte_io, SAMPLE_RATE, np_audio)
    byte_io.seek(0)
    return sr.AudioFile(byte_io)

def listen(duration=4):
    np_audio = record_audio(duration)
    with audio_data_from_numpy(np_audio) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio).lower()
    except sr.UnknownValueError:
        return ""
    except Exception as e:
        print("Recognition Error:", e)
        return ""

def capture_image(filename="/tmp/pi_image.jpg"):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to capture image")
        return None
    cv2.imwrite(filename, frame)
    print(f"Image saved to {filename}")
    return filename

def ask_openai(question):
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
        os.remove(image_path)
        return description
    except Exception as e:
        print("OpenAI image analysis error:", e)
        return "Sorry, I couldn't analyze the image."

# ---------------- MAIN LOOP ----------------
def assistant_loop():
    print("🚗 Pi Assistant started. Say a wake word...")
    while True:
        text = listen(duration=2)
        print("Heard:", text)

        if any(wake_word in text for wake_word in WAKE_WORDS):
            print("Wake word detected!")
            # Focus eyes on center immediately
            focus_thread = threading.Thread(target=focus_center, args=(3,))
            focus_thread.start()

            # Speak Yes? while listening for command
            feedback_thread = threading.Thread(target=speak, args=("Yes?",))
            feedback_thread.start()

            command_text = listen(duration=6)
            print("Command heard:", command_text)

            if any(cmd in command_text for cmd in VISION_COMMANDS):
                img_path = capture_image()
                if img_path:
                    # Show captured image on screen for 5 seconds
                    img_thread = threading.Thread(target=show_image, args=(img_path, 5))
                    img_thread.start()
                    reply = analyze_image_with_openai(img_path)
                    print("? Bot:", reply)
                    speak(reply)
                continue

            if command_text:
                reply = ask_openai(command_text)
                print("? Bot:", reply)
                speak(reply)

# ---------------- RUN ----------------
if __name__ == "__main__":
    # Start assistant loop in a separate thread
    assistant_thread = threading.Thread(target=assistant_loop, daemon=True)
    assistant_thread.start()

    # Start the eye animation (from car_eyes.py)
    import car_eyes
    car_eyes.run_eyes()
