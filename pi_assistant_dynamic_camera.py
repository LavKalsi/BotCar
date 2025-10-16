# -----------------------------------------------------------
# pi_assistant_dynamic_multimodal_controller_http_camera.py
# Raspberry Pi AI Car Assistant — Compatible with car_wifi_control_ui.py
# Smart multimodal voice + vision + movement handling
# -----------------------------------------------------------

import speech_recognition as sr
import sounddevice as sd
import numpy as np
import io
import scipy.io.wavfile as wav
import subprocess
import base64
import os
from threading import Thread
from openai import OpenAI
import requests
from car_motion_controller import move_forward, move_backward, move_left, move_right, stop  # Motor control
import socket

# ---------------- CONFIG ----------------
SAMPLE_RATE = 16000
WAKE_WORDS = ["hello","care bot", "hey", "computer", "buddy", "hi", "smart mirror"]

# Initialize OpenAI client (set your key as environment variable)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

recognizer = sr.Recognizer()

# ---------------- UTILITIES ----------------
def speak(text):
    """Speak text asynchronously and print a controller marker."""
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
    """Convert numpy audio to AudioFile object."""
    byte_io = io.BytesIO()
    wav.write(byte_io, SAMPLE_RATE, np_audio)
    byte_io.seek(0)
    return sr.AudioFile(byte_io)

def listen(duration=4):
    """Record and recognize voice input."""
    np_audio = record_audio(duration)
    with audio_data_from_numpy(np_audio) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"Heard: {text}", flush=True)
        return text
    except sr.UnknownValueError:
        print("Heard: ", flush=True)
        return ""
    except Exception as e:
        print("Heard: ", flush=True)
        print("Recognition Error:", e, flush=True)
        return ""

# ---------------- AUTO DETECT WIFI SERVER IP ----------------
def get_local_ip():
    """Get the Raspberry Pi local IP address on the network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

CAR_WIFI_IP = get_local_ip()
CAPTURE_URL = f"http://{CAR_WIFI_IP}:5000/capture"
print(f"[INFO] Using WiFi server IP: {CAR_WIFI_IP}", flush=True)

# ---------------- CAMERA ----------------
def capture_image(filename="/tmp/pi_image.jpg"):
    """Request a single frame from the WiFi control server."""
    try:
        resp = requests.get(CAPTURE_URL, timeout=5)
        if resp.status_code == 200:
            with open(filename, "wb") as f:
                f.write(resp.content)
            print(f"Image saved to {filename}", flush=True)
            return filename
        else:
            print(f"Failed to capture image, status code: {resp.status_code}", flush=True)
            return None
    except Exception as e:
        print("Error fetching image from WiFi server:", e, flush=True)
        return None

def analyze_image_with_openai(image_path, user_command="Describe what you see"):
    """Send image to OpenAI for vision analysis."""
    try:
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a playful AI pet that can see through the car camera. "
                        "Always describe the image naturally and briefly (1–2 sentences)."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_command},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}},
                    ],
                },
            ],
            max_tokens=250,
        )

        description = response.choices[0].message.content.strip()
        os.remove(image_path)
        return description
    except Exception as e:
        print("OpenAI image analysis error:", e, flush=True)
        return "Sorry, I couldn't analyze the image."

# ---------------- OPENAI CHAT ----------------
def ask_openai(question):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly, playful AI pet that lives in a car."},
                {"role": "user", "content": question},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI API Error:", e, flush=True)
        return "Sorry, I couldn't get a response."

# ---------------- COMMAND CLASSIFICATION ----------------
def classify_command(command_text, category):
    try:
        prompt = (
            f"You are an AI that decides if a command relates to {category}. "
            f"Answer only 'yes' or 'no'. 'Vision' means looking, seeing, detecting, describing. "
            f"'Movement' means driving, turning, stopping, going, or any motion.\n\nCommand: {command_text}"
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return "yes" in response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Error classifying {category}:", e, flush=True)
        return False

def interpret_command(command_text):
    """Quick interpretation."""
    text = command_text.lower()
    vision_keywords = ["see", "look", "detect", "what am i", "recognize", "scan", "describe", "camera", "how do i look"]
    move_keywords = ["move", "go", "turn", "forward", "back", "left", "right", "reverse", "drive", "stop"]

    if any(k in text for k in vision_keywords):
        return "vision"
    if any(k in text for k in move_keywords):
        return "movement"

    if classify_command(text, "vision"):
        return "vision"
    elif classify_command(text, "movement"):
        return "movement"
    else:
        return "general"

# ---------------- HANDLERS ----------------
def handle_vision_command(command_text):
    img_path = capture_image()
    if img_path:
        if any(k in command_text for k in ["how do i look", "am i", "face", "selfie"]):
            prompt = "Describe how the person looks or what they are holding."
        elif "outside" in command_text or "front" in command_text:
            prompt = "Describe what’s in front of the car."
        else:
            prompt = command_text

        reply = analyze_image_with_openai(img_path, prompt)
        print(f"? Bot: {reply}", flush=True)
        speak(reply)

def handle_movement_command(command_text):
    text = command_text.lower().strip()
    short_move = any(kw in text for kw in ["a little", "a bit", "short", "slightly", "tiny", "small"])
    long_move = any(kw in text for kw in ["keep moving", "for a while", "longer", "continue", "go on"])
    duration = 1.0 if short_move else 2.5 if long_move else 1.5

    if any(kw in text for kw in ["back", "reverse", "behind"]):
        speak("Moving backward!"); move_backward(duration); return
    if any(kw in text for kw in ["left", "turn left", "go left"]):
        speak("Turning left!"); move_left(duration); return
    if any(kw in text for kw in ["right", "turn right", "go right"]):
        speak("Turning right!"); move_right(duration); return
    if any(kw in text for kw in ["stop", "halt", "wait", "pause"]):
        speak("Stopping now."); stop(); return
    if any(kw in text for kw in ["forward", "ahead", "straight", "front", "go on", "go forward", "move ahead"]):
        speak("Moving forward!"); move_forward(duration); return
    if "move" in text or "go" in text or "drive" in text:
        if any(kw in text for kw in ["back", "reverse", "behind"]):
            speak("Going backward."); move_backward(duration)
        else:
            speak("Going ahead."); move_forward(duration)
        return
    speak("I'm not sure which way to move. Should I go forward or back?")

def handle_general_command(command_text):
    reply = ask_openai(command_text)
    print(f"? Bot: {reply}", flush=True)
    speak(reply)

# ---------------- MAIN LOOP ----------------
print("🚗 Pi Assistant started. Say a wake word...", flush=True)

while True:
    text = listen(duration=2)
    if any(w in text for w in WAKE_WORDS):
        print("Wake word detected!", flush=True)
        Thread(target=speak, args=("Yes?",)).start()
        command_text = listen(duration=6)
        print(f"Command heard: {command_text}", flush=True)
        if not command_text:
            speak("I didn't catch that.")
            continue

        category = interpret_command(command_text)
        if category == "vision":
            handle_vision_command(command_text)
        elif category == "movement":
            handle_movement_command(command_text)
        else:
            handle_general_command(command_text)
