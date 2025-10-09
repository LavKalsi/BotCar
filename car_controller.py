# car_controller.py
import subprocess
import threading
import time
import pyautogui
import psutil
import sys

# ---------------- CONFIG ----------------
ASSISTANT_PATH = "/home/pi5-3/SmartMirror/python/withouteyescarmic.py"
EYES_PATH = "/home/pi5-3/SmartMirror/python/car_eyes.py"

FOCUS_DURATION = 10        # seconds to stay focused after meaningful speech
EMPTY_HEARD_LIMIT = 15     # consecutive empty "Heard:" before sleep
CHECK_INTERVAL = 1         # state manager loop interval (seconds)

# ---------------- STATE ----------------
last_activity_time = time.time()
current_state = None       # 'focus', 'random', 'sleep'
empty_heard_count = 0      # count consecutive empty "Heard:"

# ---------------- LAUNCH PROCESSES ----------------
print("🚀 Starting car assistant and eyes...")
assistant_proc = subprocess.Popen(
    ["python3", "-u", ASSISTANT_PATH],  # -u = unbuffered
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)
eyes_proc = subprocess.Popen(["python3", EYES_PATH])
print("👀 Both processes launched successfully.")

# ---------------- SEND KEYPRESS ----------------
def set_state(new_state):
    """Send keypress if state is different or override current_state."""
    global current_state
    if new_state != current_state:
        current_state = new_state
        key_map = {'focus': '2', 'random': '1', 'sleep': '3'}
        key = key_map.get(new_state)
        if key:
            pyautogui.press(key)
            print(f"[EYES] Sent key '{key}' → {new_state}", flush=True)

# ---------------- MONITOR ASSISTANT OUTPUT ----------------
def monitor_assistant_output():
    """Monitor assistant stdout and detect activity."""
    global last_activity_time, empty_heard_count

    print("🔍 Monitoring assistant output for voice or AI activity...")

    for line in assistant_proc.stdout:
        if not line:
            continue

        line = line.strip()
        print(f"[MIC] {line}", flush=True)
        lower = line.lower()

        # ---- Handle Heard ----
        if "heard:" in lower:
            parts = line.split(":", 1)
            heard_text = parts[1].strip() if len(parts) > 1 else ""

            if heard_text:
                # Meaningful speech → focus immediately
                last_activity_time = time.time()
                empty_heard_count = 0
                print(f"[ACTIVITY] Focus due to speech: {heard_text}", flush=True)
                set_state('focus')
            else:
                # Empty Heard → random movement only if not sleeping
                empty_heard_count += 1
                last_activity_time = time.time()  # minor activity
                print(f"[ACTIVITY] Empty Heard detected ({empty_heard_count}/{EMPTY_HEARD_LIMIT})", flush=True)
                
                if current_state != 'sleep':
                    set_state('random')

                if empty_heard_count >= EMPTY_HEARD_LIMIT:
                    print("[ACTIVITY] Empty Heard reached limit → putting eyes to sleep", flush=True)
                    set_state('sleep')
                    empty_heard_count = 0

        # ---- Other activity triggers ----
        elif (
            "wake word detected" in lower
            or "command heard" in lower
            or "bot:" in lower
            or "[speak]" in lower
        ):
            last_activity_time = time.time()
            empty_heard_count = 0
            print(f"[ACTIVITY] Focus due to bot/user activity: {line}", flush=True)
            set_state('focus')

# ---------------- STATE MANAGER ----------------
def state_manager():
    """Update eye state based on elapsed time since last activity."""
    global last_activity_time, current_state

    while True:
        elapsed = time.time() - last_activity_time

        # Only switch to random if focus duration passed and not sleeping
        if elapsed >= FOCUS_DURATION and current_state != 'sleep':
            set_state('random')

        time.sleep(CHECK_INTERVAL)

# ---------------- THREADS ----------------
threading.Thread(target=monitor_assistant_output, daemon=True).start()
threading.Thread(target=state_manager, daemon=True).start()

print("✅ Car controller running. Watching assistant output...")

# ---------------- CLEANUP ----------------
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Exiting controller...")
    assistant_proc.terminate()
    eyes_proc.terminate()
    for proc in psutil.process_iter():
        if "python3" in proc.name():
            proc.kill()
    print("✅ All processes terminated cleanly.")
