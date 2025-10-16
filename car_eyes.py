import pygame
import sys
import random
import math
import os
import subprocess

# Initialize Pygame
pygame.init()

# Get display size (fullscreen)
SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("RoboEyes Actions Fully Parameterized")

# ---------------- COLORS ----------------
WHITE = (245, 245, 245)
BLACK = (0, 0, 0)
DEFAULT_IRIS_COLOR = (101, 67, 33)
DEFAULT_ZZZ_COLOR = (30, 144, 255)
CHEEK_COLOR = (255, 182, 193)
BUTTON_COLOR = (200, 200, 200)
BUTTON_TEXT_COLOR = (0, 0, 0)

# ---------------- SCALING ----------------
BASE_WIDTH = 800
BASE_HEIGHT = 480
scale_x = SCREEN_WIDTH / BASE_WIDTH
scale_y = SCREEN_HEIGHT / BASE_HEIGHT

# ---------------- EYE PARAMETERS ----------------
eye_radius = int(80 * min(scale_x, scale_y))  # size of eye
pupil_radius = int(30 * min(scale_x, scale_y))  # size of pupil
eye_y = SCREEN_HEIGHT // 2 - 50  # vertical center of eyes
left_eye_x = SCREEN_WIDTH // 3   # x position of left eye
right_eye_x = 2 * SCREEN_WIDTH // 3  # x position of right eye
eye_outline_thickness = 4  # thickness of the black border

# ---------------- MOUTH PARAMETERS ----------------
mouth_width = int(150 * scale_x)  # horizontal width of smile arc
mouth_height = int(60 * scale_y)  # vertical height of smile arc
mouth_y = eye_y + eye_radius + 140  # vertical position of mouth for smile/frown
focus_mouth_offset = 20  # extra offset to lower circle mouth in focus mode

# ---------------- CHEEKS PARAMETERS ----------------
cheek_radius = int(35 * min(scale_x, scale_y))
cheek_offset_y = 160  # vertical offset from eye center
left_cheek_x = left_eye_x - 80
right_cheek_x = right_eye_x + 80
cheek_y = eye_y + cheek_offset_y

# ---------------- CLOCK ----------------
clock = pygame.time.Clock()
FPS = 60

# ---------------- HELPER FUNCTIONS ----------------
def lerp(a, b, t):
    return a + (b - a) * t

def draw_eye(cx, cy, pupil_x, pupil_y, iris_color=DEFAULT_IRIS_COLOR, blink=False):
    """Draws a single eye with optional blink."""
    if not blink:
        pygame.draw.circle(screen, WHITE, (cx, cy), eye_radius)
        pygame.draw.circle(screen, iris_color, (int(pupil_x), int(pupil_y)), pupil_radius)
        pygame.draw.circle(screen, BLACK, (int(pupil_x), int(pupil_y)), pupil_radius // 2)
        pygame.draw.circle(screen, BLACK, (cx, cy), eye_radius, eye_outline_thickness)
    else:
        pygame.draw.line(screen, BLACK, (cx - eye_radius, cy), (cx + eye_radius, cy), 6)

def draw_mouth(action):
    """Draws the mouth depending on action."""
    if action == "focus":
        # Circle mouth lower than other mouths
        pygame.draw.circle(screen, BLACK, (SCREEN_WIDTH//2, mouth_y + focus_mouth_offset), int(mouth_height//2))
    else:
        # Smile/frown mouth
        rect = pygame.Rect(0, 0, mouth_width, mouth_height)
        rect.center = (SCREEN_WIDTH//2, mouth_y)
        pygame.draw.arc(screen, BLACK, rect, math.pi + math.pi/6, 2*math.pi - math.pi/6, 6)

def draw_cheeks():
    """Draws cheeks below eyes."""
    pygame.draw.circle(screen, CHEEK_COLOR, (left_cheek_x, cheek_y), cheek_radius)
    pygame.draw.circle(screen, CHEEK_COLOR, (right_cheek_x, cheek_y), cheek_radius)

def random_target():
    """Random pupil target offset within eye."""
    dx = random.uniform(-(eye_radius - pupil_radius), (eye_radius - pupil_radius))
    dy = random.uniform(-(eye_radius - pupil_radius), (eye_radius - pupil_radius))
    return dx, dy

def random_look(left_pupil, right_pupil, target_offset):
    desired_left = [left_eye_x + target_offset[0], eye_y + target_offset[1]]
    desired_right = [right_eye_x + target_offset[0], eye_y + target_offset[1]]
    return desired_left, desired_right

def focus_center(left_pupil, right_pupil):
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2 - 50
    desired_left = [center_x - (right_eye_x - left_eye_x)//2, center_y]
    desired_right = [center_x + (right_eye_x - left_eye_x)//2, center_y]
    return desired_left, desired_right

def sleep_action(zzz_color=DEFAULT_ZZZ_COLOR):
    """Draw closed eyes with Z's for sleep action."""
    pygame.draw.line(screen, BLACK, (left_eye_x - eye_radius, eye_y), (left_eye_x + eye_radius, eye_y), 6)
    pygame.draw.line(screen, BLACK, (right_eye_x - eye_radius, eye_y), (right_eye_x + eye_radius, eye_y), 6)
    
    font_offset_y = int(math.sin(pygame.time.get_ticks()/500)*10)
    z_sizes = [int(60*min(scale_x, scale_y)), int(45*min(scale_x, scale_y)), int(30*min(scale_x, scale_y))]
    z_positions = [(60*scale_x, -100*scale_y), (80*scale_x, -130*scale_y), (100*scale_x, -160*scale_y)]

    for i, size in enumerate(z_sizes):
        z_font = pygame.font.SysFont(None, size)
        z_text = z_font.render("Z", True, zzz_color)
        z_text = pygame.transform.rotate(z_text, 20)
        rect = z_text.get_rect(center=(right_eye_x + z_positions[i][0], eye_y + z_positions[i][1] + font_offset_y))
        screen.blit(z_text, rect)

# ---------------- NEW FUNCTIONS ----------------
def minimize_eyes():
    """Minimizes the Pygame window to show Pi desktop."""
    try:
        pygame.display.iconify()
    except Exception as e:
        print("Error minimizing eyes:", e)

def show_qr_code():
    """Calls external script to generate QR code."""
    try:
        subprocess.Popen([sys.executable, "/home/pi5-3/car/fulltest/show_qr.py"])
    except Exception as e:
        print("Error showing QR code:", e)

# ---------------- INITIAL PUPILS ----------------
left_pupil = [left_eye_x, eye_y]
right_pupil = [right_eye_x, eye_y]
target_offset = random_target()

actions = ["random", "focus", "sleep"]
current_action = "random"

blink_counter = 0
blink_duration = 10
blinking = False

iris_color = DEFAULT_IRIS_COLOR
zzz_color = DEFAULT_ZZZ_COLOR

# ---------------- BUTTONS ----------------
button_font = pygame.font.SysFont(None, int(35 * min(scale_x, scale_y)))
min_btn = pygame.Rect(20, 20, 160, 50)
qr_btn = pygame.Rect(200, 20, 200, 50)

# ---------------- MAIN LOOP ----------------
running = True
while running:
    screen.fill(WHITE)

    # --- Draw buttons ---
    pygame.draw.rect(screen, BUTTON_COLOR, min_btn, border_radius=10)
    pygame.draw.rect(screen, BUTTON_COLOR, qr_btn, border_radius=10)
    screen.blit(button_font.render("Minimize", True, BUTTON_TEXT_COLOR), (30, 30))
    screen.blit(button_font.render("  Show QR", True, BUTTON_TEXT_COLOR), (210, 30))

    # --- Event handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                current_action = "random"
            elif event.key == pygame.K_2:
                current_action = "focus"
            elif event.key == pygame.K_3:
                current_action = "sleep"
            elif event.key == pygame.K_b:
                zzz_color = (30, 144, 255)
            elif event.key == pygame.K_r:
                zzz_color = (255, 0, 0)
            elif event.key == pygame.K_g:
                zzz_color = (0, 255, 0)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if min_btn.collidepoint(mx, my):
                minimize_eyes()
            elif qr_btn.collidepoint(mx, my):
                show_qr_code()

    # ---------------- BLINK ----------------
    blink_counter += 1
    if blink_counter > 300:
        blinking = True
    if blinking and blink_counter > 300 + blink_duration:
        blinking = False
        blink_counter = 0

    # ---------------- ACTIONS ----------------
    if current_action == "random":
        if random.randint(0, 100) < 2:
            target_offset = random_target()
        desired_left, desired_right = random_look(left_pupil, right_pupil, target_offset)
    elif current_action == "focus":
        desired_left, desired_right = focus_center(left_pupil, right_pupil)
    elif current_action == "sleep":
        desired_left, desired_right = [left_pupil, right_pupil]
        sleep_action(zzz_color=zzz_color)

    if current_action != "sleep":
        left_pupil[0] = lerp(left_pupil[0], desired_left[0], 0.015)
        left_pupil[1] = lerp(left_pupil[1], desired_left[1], 0.015)
        right_pupil[0] = lerp(right_pupil[0], desired_right[0], 0.015)
        right_pupil[1] = lerp(right_pupil[1], desired_right[1], 0.015)

    if current_action != "sleep":
        draw_eye(left_eye_x, eye_y, left_pupil[0], left_pupil[1], iris_color, blink=blinking)
        draw_eye(right_eye_x, eye_y, right_pupil[0], right_pupil[1], iris_color, blink=blinking)

    draw_mouth(current_action)
    draw_cheeks()

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
