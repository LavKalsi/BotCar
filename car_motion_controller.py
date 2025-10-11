# car_motion_controller.py
# Car motor control using gpiozero — compatible with Raspberry Pi 5

from gpiozero import OutputDevice
from time import sleep

# ====== MOTOR PIN SETUP ======
# These are your L298N or similar motor driver control pins
motor_pins = {
    "IN1": 17,
    "IN2": 18,
    "IN3": 22,
    "IN4": 23
}

# Create OutputDevice objects for each pin
IN1 = OutputDevice(motor_pins["IN1"])
IN2 = OutputDevice(motor_pins["IN2"])
IN3 = OutputDevice(motor_pins["IN3"])
IN4 = OutputDevice(motor_pins["IN4"])

# ====== MOTOR CONTROL FUNCTIONS ======
def set_motor_state(in1, in2, in3, in4):
    IN1.value = in1
    IN2.value = in2
    IN3.value = in3
    IN4.value = in4

def move_forward(duration=1):
    print("🚗 Moving forward")
    set_motor_state(1, 0, 1, 0)
    sleep(duration)
    stop()

def move_backward(duration=1):
    print("🚗 Moving backward")
    set_motor_state(0, 1, 0, 1)
    sleep(duration)
    stop()

def move_left(duration=1):
    print("↩️ Turning left")
    set_motor_state(0, 1, 1, 0)
    sleep(duration)
    stop()

def move_right(duration=1):
    print("↪️ Turning right")
    set_motor_state(1, 0, 0, 1)
    sleep(duration)
    stop()

def stop():
    print("🛑 Stopping")
    set_motor_state(0, 0, 0, 0)

# ====== CLEANUP ======
def cleanup():
    stop()
    print("🔌 Cleaning up GPIO resources")

# ====== TEST MODE ======
if __name__ == "__main__":
    try:
        move_forward()
        move_backward()
        move_left()
        move_right()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
