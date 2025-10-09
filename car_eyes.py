import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("RoboEyes Actions")

# Colors
WHITE = (245, 245, 245)      # off-white eye
BLACK = (0, 0, 0)
DEFAULT_IRIS_COLOR = (101, 67, 33)  # dark brown iris
DEFAULT_ZZZ_COLOR = (30, 144, 255)  # default ZZZ color (blue)

# Eye settings
eye_radius = 100
pupil_radius = 30
eye_y = SCREEN_HEIGHT // 2
left_eye_x = SCREEN_WIDTH // 3
right_eye_x = 2 * SCREEN_WIDTH // 3

# Clock
clock = pygame.time.Clock()
FPS = 60

# Linear interpolation
def lerp(a, b, t):
    return a + (b - a) * t

# Draw single eye
def draw_eye(cx, cy, pupil_x, pupil_y, iris_color=DEFAULT_IRIS_COLOR, blink=False):
    if not blink:
        # Eye white
        pygame.draw.circle(screen, WHITE, (cx, cy), eye_radius)
        # Iris
        pygame.draw.circle(screen, iris_color, (int(pupil_x), int(pupil_y)), pupil_radius)
        # Pupil (inner)
        pygame.draw.circle(screen, BLACK, (int(pupil_x), int(pupil_y)), pupil_radius // 2)
        # Eye outline
        pygame.draw.circle(screen, BLACK, (cx, cy), eye_radius, 4)
    else:
        # Closed eye
        pygame.draw.line(screen, BLACK, (cx - eye_radius, cy), (cx + eye_radius, cy), 6)

# Random target offset for random_look
def random_target():
    dx = random.uniform(-(eye_radius - pupil_radius), (eye_radius - pupil_radius))
    dy = random.uniform(-(eye_radius - pupil_radius), (eye_radius - pupil_radius))
    return dx, dy

# Actions
def random_look(left_pupil, right_pupil, target_offset):
    desired_left = [left_eye_x + target_offset[0], eye_y + target_offset[1]]
    desired_right = [right_eye_x + target_offset[0], eye_y + target_offset[1]]
    return desired_left, desired_right

def focus_center(left_pupil, right_pupil):
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2
    desired_left = [center_x - (right_eye_x - left_eye_x)//2, center_y]
    desired_right = [center_x + (right_eye_x - left_eye_x)//2, center_y]
    return desired_left, desired_right

def sleep_action(zzz_color=DEFAULT_ZZZ_COLOR):
    # Eyes closed
    pygame.draw.line(screen, BLACK, (left_eye_x - eye_radius, eye_y), (left_eye_x + eye_radius, eye_y), 6)
    pygame.draw.line(screen, BLACK, (right_eye_x - eye_radius, eye_y), (right_eye_x + eye_radius, eye_y), 6)
    
    # Floating tilted ZZZ above right eye
    font = pygame.font.SysFont(None, 50)
    offset_y = int(math.sin(pygame.time.get_ticks()/500)*10)

    # Z sizes: first largest, middle smaller, last smallest
    z_sizes = [60, 45, 30]  # font sizes
    z_positions = [(60, -100), (80, -130), (100, -160)]  # relative offsets from eye center

    for i, size in enumerate(z_sizes):
        z_font = pygame.font.SysFont(None, size)
        z_text = z_font.render("Z", True, zzz_color)
        z_text = pygame.transform.rotate(z_text, 20)  # tilt 20 degrees
        rect = z_text.get_rect(center=(right_eye_x + z_positions[i][0], eye_y + z_positions[i][1] + offset_y))
        screen.blit(z_text, rect)


# Initial pupil positions
left_pupil = [left_eye_x, eye_y]
right_pupil = [right_eye_x, eye_y]
target_offset = random_target()

# Action selector
actions = ["random", "focus", "sleep"]
current_action = "random"

# Blink logic
blink_counter = 0
blink_duration = 10
blinking = False

# Iris color
iris_color = DEFAULT_IRIS_COLOR

# ZZZ color (changeable)
zzz_color = DEFAULT_ZZZ_COLOR

# Main loop
running = True
while running:
    screen.fill((30, 30, 30))  # dark background

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Change action with keys
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                current_action = "random"
            elif event.key == pygame.K_2:
                current_action = "focus"
            elif event.key == pygame.K_3:
                current_action = "sleep"
            # Change ZZZ color for demo
            elif event.key == pygame.K_b:
                zzz_color = (30, 144, 255)  # blue
            elif event.key == pygame.K_r:
                zzz_color = (255, 0, 0)     # red
            elif event.key == pygame.K_g:
                zzz_color = (0, 255, 0)     # green

    # Update blink
    blink_counter += 1
    if blink_counter > 300:
        blinking = True
    if blinking and blink_counter > 300 + blink_duration:
        blinking = False
        blink_counter = 0

    # Determine desired pupil positions
    if current_action == "random":
        # Occasionally pick new target
        if random.randint(0, 100) < 2:
            target_offset = random_target()
        desired_left, desired_right = random_look(left_pupil, right_pupil, target_offset)
    elif current_action == "focus":
        desired_left, desired_right = focus_center(left_pupil, right_pupil)
    elif current_action == "sleep":
        desired_left, desired_right = [left_pupil, right_pupil]  # don't move
        sleep_action(zzz_color=zzz_color)

    # Smooth pupil movement (slower for random)
    if current_action != "sleep":
        left_pupil[0] = lerp(left_pupil[0], desired_left[0], 0.015)  # slower than before
        left_pupil[1] = lerp(left_pupil[1], desired_left[1], 0.015)
        right_pupil[0] = lerp(right_pupil[0], desired_right[0], 0.015)
        right_pupil[1] = lerp(right_pupil[1], desired_right[1], 0.015)

    # Draw eyes (skip if sleeping)
    if current_action != "sleep":
        draw_eye(left_eye_x, eye_y, left_pupil[0], left_pupil[1], iris_color, blink=blinking)
        draw_eye(right_eye_x, eye_y, right_pupil[0], right_pupil[1], iris_color, blink=blinking)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
