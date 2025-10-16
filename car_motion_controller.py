# car_motion_controller.py
# Redirects motor commands to car_wifi_control.py via HTTP requests
# Automatically detects Raspberry Pi IP

import requests
import time
import socket

# ====== HELPER: GET LOCAL IP ======
def get_local_ip():
    """Get the Raspberry Pi local IP address automatically."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Doesn't actually connect, just gets IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

PI_IP = get_local_ip()
CAR_CONTROL_URL = f"http://{PI_IP}:5000/move"
print(f"Using Flask server at {CAR_CONTROL_URL}")

# ====== SEND MOVE COMMAND ======
def send_move_command(direction, duration=None):
    """
    Send movement command to the Flask server.
    direction: "forward", "backward", "left", "right", "stop"
    duration: if specified, stops the movement after that many seconds
    """
    try:
        # Start movement
        requests.post(CAR_CONTROL_URL, json={"command": direction, "action": "start"})
        if duration:
            time.sleep(duration)
            # Stop movement after duration
            requests.post(CAR_CONTROL_URL, json={"command": "stop", "action": "stop"})
    except Exception as e:
        print("Error sending move command:", e)

# ====== MOTOR FUNCTIONS ======
def move_forward(duration=1):
    print("🚗 Moving forward")
    send_move_command("forward", duration)

def move_backward(duration=1):
    print("🚗 Moving backward")
    send_move_command("backward", duration)

def move_left(duration=1):
    print("↩️ Turning left")
    send_move_command("left", duration)

def move_right(duration=1):
    print("↪️ Turning right")
    send_move_command("right", duration)

def stop():
    print("🛑 Stopping")
    send_move_command("stop")

# ====== TEST MODE ======
if __name__ == "__main__":
    try:
        move_forward(1)
        move_backward(1)
        move_left(1)
        move_right(1)
        stop()
    except KeyboardInterrupt:
        print("Exiting test.")
