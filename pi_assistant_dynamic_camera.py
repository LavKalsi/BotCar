# pi_assistant_dynamic_multimodal_controller_compatible.py
# Raspberry Pi AI Car Assistant — compatible with car_controller.py
# Dynamic multi-category commands + vision + speech-controlled movement

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
from car_motion_controller import move_forward, move_backward, move_left, move_right, stop  # 🆕 Motor control import

# ---------------- CONFIG ----------------
SAMPLE_RATE = 16000
WAKE_WORDS = ["hello", "hey", "computer", "buddy", "hi", "smart mirror"]

# Initialize OpenAI client
client = OpenAI(api_key="")  # 🔑 Replace with your real key

# Initialize recognizer
recognizer = sr.Recognizer()

# ---------------- UTILS ----------------
def speak(text):
    """Speak text asynchronously using espeak and print marker for car_controller."""
    if not text:
        return
    print(f"[SPEAK] {text}", flush=True)
    subprocess.Popen(["espeak", "-v", "en-us", "-s", "200", text])

def record_audio(duration):
    """Record audio from mic."""
    print(f"? Recording for {duration} seconds...", flush=True)
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
        text = recognizer.recognize_google(audio).lower()
        print(f"Heard: {text}", flush=True)
        return text
    except sr.UnknownValueError:
        print(f"Heard: ", flush=True)
        return ""
    except Exception as e:
        print(f"Heard: ", flush=True)
        print("Recognition Error:", e, flush=True)
        return ""

# ---------------- CAMERA ----------------
def capture_image(filename="/tmp/pi_image.jpg"):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to capture image", flush=True)
        return None
    cv2.imwrite(filename, frame)
    print(f"Image saved to {filename}", flush=True)
    return filename

def analyze_image_with_openai(image_path, user_command="Describe what you see"):
    try:
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a playful AI pet living inside a car. "
                        "You can see through the car's camera and describe what you see like a curious companion. "
                        "Never say you are virtual or cannot see — always describe what’s in the image. "
                        "Be expressive but brief (1–2 sentences max)."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_command},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                    ]
                }
            ],
            max_tokens=250,
        )

        description = response.choices[0].message.content.strip()
        os.remove(image_path)
        return description
    except Exception as e:
        print("OpenAI image analysis error:", e, flush=True)
        return "Sorry, I couldn't analyze the image."

# ---------------- OPENAI ----------------
def ask_openai(question):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly, playful AI pet that lives in a car."},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI API Error:", e, flush=True)
        return "Sorry, I couldn't get a response."

# ---------------- COMMAND CLASSIFICATION ----------------
def classify_command(command_text, category):
    try:
        prompt = (
            f"You are an AI that classifies commands into the category '{category}'. "
            "Answer only 'yes' or 'no'. No punctuation, no explanation.\n\n"
            f"Command: \"{command_text}\""
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a command classifier."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        answer = response.choices[0].message.content.strip().lower()
        return "yes" in answer
    except Exception as e:
        print(f"Error classifying {category}:", e, flush=True)
        return False

# ---------------- COMMAND HANDLERS ----------------
def handle_vision_command(command_text):
    img_path = capture_image()
    if img_path:
        reply = analyze_image_with_openai(img_path, command_text)
        print(f"? Bot: {reply}", flush=True)
        speak(reply)

def handle_movement_command(command_text):
    """Handle movement like forward, backward, left, right, stop."""
    command_text = command_text.lower()
    if "forward" in command_text:
        speak("Moving forward!")
        move_forward()
    elif "backward" in command_text or "reverse" in command_text:
        speak("Moving backward!")
        move_backward()
    elif "left" in command_text:
        speak("Turning left!")
        move_left()
    elif "right" in command_text:
        speak("Turning right!")
        move_right()
    elif "stop" in command_text:
        speak("Stopping now.")
        stop()
    else:
        speak("I didn’t understand that movement command.")

def handle_general_command(command_text):
    reply = ask_openai(command_text)
    print(f"? Bot: {reply}", flush=True)
    speak(reply)

# ---------------- MAIN LOOP ----------------
print("🚗 Pi Assistant started. Say a wake word...", flush=True)

while True:
    text = listen(duration=2)
    if any(wake_word in text for wake_word in WAKE_WORDS):
        print("Wake word detected!", flush=True)
        Thread(target=speak, args=("Yes?",)).start()

        command_text = listen(duration=6)
        print(f"Command heard: {command_text}", flush=True)

        if not command_text:
            speak("I didn't catch that.")
            continue

        # Handle categories dynamically
        if classify_command(command_text, "vision"):
            handle_vision_command(command_text)
        elif classify_command(command_text, "movement"):
            handle_movement_command(command_text)
        else:
            handle_general_command(command_text)
