# 🤖 Raspberry Pi Smart Car (AI Voice + Vision + Wi-Fi Control)

This project turns your **Raspberry Pi** into an **AI-powered robot car** that can:
- 🎙️ Listen and respond to voice commands
- 👁️ See using a camera and describe its surroundings
- 🚗 Move forward, backward, left, and right using GPIO motor control
- 🌐 Be controlled remotely via a **Flask-based Wi-Fi Web UI**
- 🧠 Use OpenAI for intelligent conversation and visual understanding

---

## 🧩 Project Structure

| File | Description |
|------|-------------|
| car_controller.py | Main orchestrator that launches all subsystems |
| pi_assistant_dynamic_camera.py | AI assistant: handles voice, vision, and commands |
| car_motion_controller.py | Sends movement commands via HTTP to the Wi-Fi control server |
| car_wifi_control.py | Flask server controlling GPIO motor pins and camera streaming |
| car_eyes.py | Optional visual display showing "eyes" and expressions |


## ⚙️ Hardware Requirements

- Raspberry Pi 3 / 4 / 5
- L298N or L293D motor driver module
- 2 DC motors (left + right)
- USB microphone
- USB camera (e.g. Logitech or Pi Camera)
- Power supply
- Jumper wires

---

## 🪛 Wiring Diagram (GPIO to Motor Driver)

**Motor Driver → Raspberry Pi GPIO Pins**

| Motor Driver Pin | Raspberry Pi Pin / Function      |
|-----------------|---------------------------------|
| IN1             | GPIO17 (Pin 11)                |
| IN2             | GPIO18 (Pin 12)                |
| IN3             | GPIO22 (Pin 15)                |
| IN4             | GPIO23 (Pin 16)                |
| ENA             | 5V (Enable left motor)         |
| ENB             | 5V (Enable right motor)        |
| GND             | Pi GND (Pin 6)                 |

**Notes:**
- Motor A → Left wheels  
- Motor B → Right wheels


## 🧠 Software Features

| Component | Description |
|------------|-------------|
| `pi_assistant_dynamic_camera.py` | Handles speech recognition, wake words, AI chat, camera vision |
| `car_motion_controller.py` | Sends movement commands to Wi-Fi control via HTTP |
| `car_wifi_control.py` | Controls GPIO motor pins, streams live camera feed |
| `car_controller.py` | Master file that launches all processes together |
| `car_eyes.py` | Visual “eyes” animation (optional display) |

---

## 🧩 Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<yourusername>/raspberry-pi-ai-car.git
cd raspberry-pi-ai-car
```
### 2️⃣ Create a virtual environment
```bash
python3 -m venv ~/car/env
source ~/car/env/bin/activate
```
### 3️⃣ Install dependencies
```bash
pip install flask requests gpiozero opencv-python pyautogui speechrecognition sounddevice numpy scipy openai psutil
sudo apt install espeak -y
```
## 🔑 Set Your OpenAI API Key
Add your OpenAI key to the environment:

```bash
export OPENAI_API_KEY="your_api_key_here"
```
(Optional) Add it permanently:

```bash
echo 'export OPENAI_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```
## 🚀 Run the Car Manually
Activate the virtual environment and start the main controller:

```bash
source ~/car/env/bin/activate
python3 /home/pi5-3/carV2/fulltest/car_controller.py
```
This launches:

AI Assistant (voice & camera)

Car Eyes

Wi-Fi Flask Control

## 🌐 Access the Wi-Fi Controller UI
Once running, open a browser on your PC or phone:

```cpp
http://<your_raspberry_pi_ip>:5000
```
You’ll see:

Live camera feed

Direction buttons (⬆️⬇️⬅️➡️🛑)

⚙️ Auto Start with PM2
Install PM2
```bash
sudo npm install pm2@latest -g
```
Start your car controller with PM2
```bash
pm2 start /home/pi5-3/carV2/fulltest/car_controller.py \
  --name car_controller \
  --interpreter /home/pi5-3/car/env/bin/python
```
Make it run on boot
```bash
pm2 startup
pm2 save
sudo reboot
```
After reboot, the AI car will start automatically 🎉

## 🧪 Test Movement Commands
In a Python shell:
```bash
from car_motion_controller import move_forward, move_backward, move_left, move_right, stop
move_forward(1)
move_backward(1)
move_left(1)
move_right(1)
stop()
```
## 🧠 Example Voice Commands

| 🎤 Command | 🤖 Behavior |
|------------|-------------|
| "Hey buddy" | Wake word trigger |
| "Move forward" | Moves car forward |
| "Turn right" | Turns car right |
| "Stop" | Stops all motors |
| "What do you see?" | Captures camera image, sends to OpenAI for description |
| "Hello" | Friendly AI response |


## 🖼️ AI Vision Demo
When you say "What do you see?", the Pi:

Captures a frame from its camera

Sends it to OpenAI Vision API

Speaks a short description aloud using espeak

## 🧰 Troubleshooting

| 🐞 Issue | 🛠️ Possible Fix |
|----------|------------------|
| **ModuleNotFoundError for packages** | Make sure you are inside the correct virtual environment (`source ~/car/env/bin/activate`) |
| **Flask web UI not opening** | Check that your Raspberry Pi IP is correct (`hostname -I`) and that port `5000` is open |
| **Motors not moving** | Verify GPIO wiring, motor driver connections, and ensure the 5V power supply is connected |
| **No camera feed** | Make sure your camera is properly connected and accessible under `/dev/video0` |
| **Speech not detected** | Confirm your USB microphone is recognized (`arecord -l`) and volume levels are correct |
| **OpenAI API error** | Check your API key setup (`echo $OPENAI_API_KEY`) and ensure you have an internet connection |
| **Car moving erratically** | Double-check motor polarity and wiring order (IN1–IN4) on the L298N board |
| **Slow performance** | Close unnecessary background processes or try reducing camera resolution in `car_wifi_control.py` |


## 🧑‍💻 Credits
Developed by **Lav Kalsi**

Powered by OpenAI GPT-4o-mini

Built for Raspberry Pi with ❤️

## 📜 License
MIT License — free to use and modify.

