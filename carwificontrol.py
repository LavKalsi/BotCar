# car_wifi_control_ui.py
from flask import Flask, Response, request, jsonify, render_template_string, send_file
from gpiozero import OutputDevice
import threading
import time
import cv2
import io

app = Flask(__name__)

# ===== GPIO MOTOR PINS =====
motor_pins = {
    "IN1": 17,  # left motor forward
    "IN2": 18,  # left motor backward
    "IN3": 22,  # right motor forward
    "IN4": 23   # right motor backward
}

IN1 = OutputDevice(motor_pins["IN1"])
IN2 = OutputDevice(motor_pins["IN2"])
IN3 = OutputDevice(motor_pins["IN3"])
IN4 = OutputDevice(motor_pins["IN4"])

# ===== MOVEMENT FUNCTIONS =====
def stop():
    IN1.off()
    IN2.off()
    IN3.off()
    IN4.off()

def move_forward():
    IN1.on()
    IN2.off()
    IN3.on()
    IN4.off()

def move_backward():
    IN1.off()
    IN2.on()
    IN3.off()
    IN4.on()

def move_left():
    IN1.off()
    IN2.on()
    IN3.on()
    IN4.off()

def move_right():
    IN1.on()
    IN2.off()
    IN3.off()
    IN4.on()

# ===== CURRENT MOVEMENT STATE =====
movement_lock = threading.Lock()
current_direction = None

def movement_loop():
    global current_direction
    while True:
        with movement_lock:
            direction = current_direction

        if direction == "forward":
            move_forward()
        elif direction == "backward":
            move_backward()
        elif direction == "left":
            move_left()
        elif direction == "right":
            move_right()
        else:
            stop()

        time.sleep(0.05)  # small delay

threading.Thread(target=movement_loop, daemon=True).start()

# ===== CAMERA SETUP =====
camera = cv2.VideoCapture(0)

def gen_frames():
    """Live stream frames for the web UI."""
    while True:
        success, frame = camera.read()
        if not success:
            continue
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def capture_frame():
    """Capture a single frame for assistant requests."""
    success, frame = camera.read()
    if not success:
        return None
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return None
    return io.BytesIO(buffer.tobytes())

# ===== FLASK ROUTES =====
@app.route('/')
def index():
    return render_template_string("""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>🚗 Car Controller</title>
<style>
body { text-align: center; font-family: Arial; background: #f0f0f0; }
img { border: 2px solid #333; margin-top: 10px; }
button { width: 100px; height: 50px; margin: 5px; font-size: 16px; }
.controls { margin-top: 10px; }
</style>
</head>
<body>
<h1>🚗 Car Controller</h1>
<img src="/camera" width="640" height="480"/>
<div class="controls">
<div>
<button onmousedown="startMove('forward', event)" onmouseup="stopMove(event)" ontouchstart="startMove('forward', event)" ontouchend="stopMove(event)">⬆️ Forward</button>
</div>
<div>
<button onmousedown="startMove('left', event)" onmouseup="stopMove(event)" ontouchstart="startMove('left', event)" ontouchend="stopMove(event)">⬅️ Left</button>
<button onmousedown="startMove('stop', event)" onmouseup="stopMove(event)" ontouchstart="startMove('stop', event)" ontouchend="stopMove(event)">🛑 Stop</button>
<button onmousedown="startMove('right', event)" onmouseup="stopMove(event)" ontouchstart="startMove('right', event)" ontouchend="stopMove(event)">➡️ Right</button>
</div>
<div>
<button onmousedown="startMove('backward', event)" onmouseup="stopMove(event)" ontouchstart="startMove('backward', event)" ontouchend="stopMove(event)">⬇️ Backward</button>
</div>
</div>

<script>
function startMove(cmd, event) {
    event.preventDefault();
    fetch('/move', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: cmd, action: 'start'})
    });
}

function stopMove(event) {
    event.preventDefault();
    fetch('/move', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: 'stop', action: 'stop'})
    });
}
</script>
</body>
</html>
""")

@app.route('/camera')
def camera_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/move', methods=['POST'])
def move():
    global current_direction
    data = request.json
    cmd = data.get('command')
    action = data.get('action', 'start')

    with movement_lock:
        if action == 'start':
            current_direction = cmd
        else:
            current_direction = None

    return jsonify({"status": "ok", "command": cmd, "action": action})

@app.route('/capture')
def capture():
    """Return a single frame as JPEG to the assistant."""
    frame_io = capture_frame()
    if frame_io is None:
        return "Failed to capture image", 500
    frame_io.seek(0)
    return send_file(frame_io, mimetype='image/jpeg')

# ===== RUN SERVER =====
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
