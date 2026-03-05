"""
Emotion Catcher — A Pygame game where you catch falling emotions to keep your balance near zero.
Run: python emotion_catcher_game.py
Requires: pygame (pip install pygame)
"""

import pygame
import random
import math
import struct
import array
import os
import sys

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

WIDTH, HEIGHT = 800, 600
FPS = 60
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (220, 50, 50)
ORANGE = (255, 165, 0)
DARK_BROWN = (101, 67, 33)
BROWN_BORDER = (60, 40, 20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Emotion Catcher")
clock = pygame.time.Clock()

# ---------------------------------------------------------------------------
# Asset helpers
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _circle_crop(img: pygame.Surface, size: int) -> pygame.Surface:
    """Crop *img* into a circle of diameter *size*, removing the background."""
    scaled = pygame.transform.smoothscale(img, (size, size))
    out = pygame.Surface((size, size), pygame.SRCALPHA)
    # Draw a white circle as the mask shape
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (size // 2, size // 2), size // 2)
    # Blit the image, then apply the circle mask via per-pixel alpha
    out.blit(scaled, (0, 0))
    # Keep only the pixels inside the circle
    final = pygame.Surface((size, size), pygame.SRCALPHA)
    for y in range(size):
        for x in range(size):
            if mask.get_at((x, y)).a > 0:
                final.set_at((x, y), out.get_at((x, y)))
    return final


def _heart_crop(img: pygame.Surface, size: int) -> pygame.Surface:
    """Crop *img* into a heart shape of *size* x *size*."""
    scaled = pygame.transform.smoothscale(img, (size, size))
    # Build a heart-shaped mask using parametric equation
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size / 2, size / 2
    # Pre-compute heart boundary via filled scanlines
    heart_pixels = set()
    steps = 500
    border_pts = []
    for i in range(steps):
        t = 2.0 * math.pi * i / steps
        # Parametric heart
        hx = 16 * math.sin(t) ** 3
        hy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        # Scale to fit in size (heart spans roughly -17..17 x -17..15)
        sx = int(cx + hx * (size / 38))
        sy = int(cy + hy * (size / 38)) - size // 10  # shift up a bit
        border_pts.append((sx, sy))
    # Fill the heart polygon on the mask
    if len(border_pts) >= 3:
        pygame.draw.polygon(mask, (255, 255, 255, 255), border_pts)
    # Apply mask
    final = pygame.Surface((size, size), pygame.SRCALPHA)
    for y in range(size):
        for x in range(size):
            if mask.get_at((x, y)).a > 0:
                final.set_at((x, y), scaled.get_at((x, y)))
    return final


def load_emoji_image(filename: str, size: int = 50, shape: str = "circle") -> pygame.Surface:
    """Load an emoji image, cropped to *shape* ('circle' or 'heart')."""
    path = os.path.join(BASE_DIR, filename)
    try:
        img = pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (200, 200, 200), (size // 2, size // 2), size // 2)
        return surf
    if shape == "heart":
        return _heart_crop(img, size)
    return _circle_crop(img, size)


# Preload emoji images
EMOJI_IMAGES = {
    "Joy": load_emoji_image("joy.jpeg"),
    "Sadness": load_emoji_image("sad.png"),
    "Anger": load_emoji_image("anger.jpeg"),
    "Fear": load_emoji_image("fear.jpeg"),
    "Love": load_emoji_image("pink heart.png", shape="heart"),
}

# ---------------------------------------------------------------------------
# Generate a short "pop" sound programmatically (880 Hz sine, 100 ms)
# ---------------------------------------------------------------------------

def generate_pop_sound() -> pygame.mixer.Sound:
    sample_rate = 44100
    duration = 0.10  # seconds
    frequency = 880
    n_samples = int(sample_rate * duration)
    max_amp = 32767
    buf = array.array("h")  # signed 16-bit
    for i in range(n_samples):
        t = i / sample_rate
        # Envelope: quick fade-out
        envelope = max(0.0, 1.0 - t / duration)
        value = int(max_amp * envelope * math.sin(2.0 * math.pi * frequency * t))
        buf.append(value)
    sound = pygame.mixer.Sound(buffer=buf)
    sound.set_volume(0.4)
    return sound


pop_sound = generate_pop_sound()

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
font_small = pygame.font.SysFont("segoeui", 20)
font_medium = pygame.font.SysFont("segoeui", 28, bold=True)
font_large = pygame.font.SysFont("segoeui", 48, bold=True)
font_hud = pygame.font.SysFont("segoeui", 22, bold=True)

# ---------------------------------------------------------------------------
# Emotion definitions
# ---------------------------------------------------------------------------

EMOTIONS = [
    {
        "name": "Joy",
        "effect": 10,
        "special": None,
        "color": (255, 215, 0),       # Gold
        "feedback": "Joy! +10",
        "feedback_color": (255, 215, 0),
    },
    {
        "name": "Sadness",
        "effect": -10,
        "special": None,
        "color": (70, 130, 180),       # Steel blue
        "feedback": "Sadness! -10",
        "feedback_color": (70, 130, 180),
    },
    {
        "name": "Anger",
        "effect": 5,
        "special": None,
        "color": (220, 50, 50),        # Red
        "feedback": "Anger! +5",
        "feedback_color": (220, 50, 50),
    },
    {
        "name": "Fear",
        "effect": -5,
        "special": None,
        "color": (128, 0, 128),        # Purple
        "feedback": "Fear! -5",
        "feedback_color": (128, 0, 128),
    },
    {
        "name": "Love",
        "effect": 0,
        "special": "reset",
        "color": (255, 105, 180),      # Pink
        "feedback": "Love! Reset \u2764",
        "feedback_color": (0, 200, 0),
    },
]

# ---------------------------------------------------------------------------
# Game objects
# ---------------------------------------------------------------------------

class Catcher:
    WIDTH = 120
    HEIGHT = 30
    SPEED = 8
    Y = 540

    def __init__(self):
        self.x = (WIDTH - self.WIDTH) // 2
        self.rect = pygame.Rect(self.x, self.Y, self.WIDTH, self.HEIGHT)

    def move(self, dx: int):
        self.x += dx
        self.x = max(0, min(WIDTH - self.WIDTH, self.x))
        self.rect.x = self.x

    def draw(self, surface: pygame.Surface):
        # Body
        pygame.draw.rect(surface, DARK_BROWN, self.rect, border_radius=10)
        # Border
        pygame.draw.rect(surface, BROWN_BORDER, self.rect, width=2, border_radius=10)
        # Label
        label = font_small.render("\U0001F3AF Catcher", True, WHITE)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)


class FallingEmotion:
    RADIUS = 25
    SPEED = 4

    def __init__(self, emotion_def: dict):
        self.emotion = emotion_def
        self.x = random.randint(self.RADIUS, WIDTH - self.RADIUS)
        self.y = -self.RADIUS
        self.image = EMOJI_IMAGES.get(emotion_def["name"])

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.RADIUS, self.y - self.RADIUS,
                           self.RADIUS * 2, self.RADIUS * 2)

    def update(self):
        self.y += self.SPEED

    def draw(self, surface: pygame.Surface):
        # Draw the pre-cropped emoji image (no background)
        if self.image:
            img_rect = self.image.get_rect(center=(self.x, self.y))
            surface.blit(self.image, img_rect)
        else:
            # Fallback coloured circle
            pygame.draw.circle(surface, self.emotion["color"], (self.x, self.y), self.RADIUS)
            pygame.draw.circle(surface, BLACK, (self.x, self.y), self.RADIUS, 2)

    def is_off_screen(self) -> bool:
        return self.y - self.RADIUS > HEIGHT


class FloatingText:
    DURATION = 60  # frames (~1 second at 60 FPS)

    def __init__(self, text: str, x: int, y: int, color: tuple):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.timer = self.DURATION

    def update(self):
        self.y -= 1.5  # drift up
        self.timer -= 1

    def draw(self, surface: pygame.Surface):
        alpha = max(0, int(255 * (self.timer / self.DURATION)))
        txt_surf = font_medium.render(self.text, True, self.color)
        # Create a surface with per-pixel alpha for fading
        fade_surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
        fade_surf.blit(txt_surf, (0, 0))
        fade_surf.set_alpha(alpha)
        rect = fade_surf.get_rect(center=(self.x, int(self.y)))
        surface.blit(fade_surf, rect)

    def is_expired(self) -> bool:
        return self.timer <= 0

# ---------------------------------------------------------------------------
# HUD Drawing
# ---------------------------------------------------------------------------

BAR_X, BAR_Y, BAR_W, BAR_H = 100, 20, 600, 30
SAFE_MIN, SAFE_MAX = -5, 5
BALANCE_MIN, BALANCE_MAX = -50, 50


def draw_balance_bar(surface: pygame.Surface, balance_value: int, stable_timer: int):
    # Background bar (grey)
    pygame.draw.rect(surface, (180, 180, 180), (BAR_X, BAR_Y, BAR_W, BAR_H), border_radius=6)

    # Colour regions: red/orange for out-of-safe, green for safe zone
    # Safe zone pixel range
    safe_left = BAR_X + int((SAFE_MIN - BALANCE_MIN) / (BALANCE_MAX - BALANCE_MIN) * BAR_W)
    safe_right = BAR_X + int((SAFE_MAX - BALANCE_MIN) / (BALANCE_MAX - BALANCE_MIN) * BAR_W)

    # Draw the whole bar in orange-red
    pygame.draw.rect(surface, ORANGE, (BAR_X + 2, BAR_Y + 2, BAR_W - 4, BAR_H - 4), border_radius=5)
    # Draw safe zone in green
    pygame.draw.rect(surface, GREEN, (safe_left, BAR_Y + 2, safe_right - safe_left, BAR_H - 4))

    # Marker for current balance
    clamped = max(BALANCE_MIN, min(BALANCE_MAX, balance_value))
    marker_x = BAR_X + int((clamped - BALANCE_MIN) / (BALANCE_MAX - BALANCE_MIN) * BAR_W)
    pygame.draw.polygon(surface, BLACK, [
        (marker_x, BAR_Y - 6),
        (marker_x - 6, BAR_Y - 14),
        (marker_x + 6, BAR_Y - 14),
    ])
    pygame.draw.rect(surface, BLACK, (marker_x - 2, BAR_Y, 4, BAR_H), border_radius=2)

    # Border
    pygame.draw.rect(surface, BLACK, (BAR_X, BAR_Y, BAR_W, BAR_H), width=2, border_radius=6)

    # Text labels
    bal_text = font_hud.render(f"Balance: {balance_value}", True, BLACK)
    surface.blit(bal_text, (BAR_X, BAR_Y + BAR_H + 6))

    stable_text = font_hud.render(f"Stable: {stable_timer}s / 30s", True, BLACK)
    surface.blit(stable_text, (BAR_X + BAR_W - stable_text.get_width(), BAR_Y + BAR_H + 6))

# ---------------------------------------------------------------------------
# Main Game
# ---------------------------------------------------------------------------

def main():
    # --- Game state ---
    balance_value = 0
    stable_timer = 0
    game_active = True
    won = False

    catcher = Catcher()
    emotions: list[FallingEmotion] = []
    floating_texts: list[FloatingText] = []

    # Spawn timer (in milliseconds)
    STABILITY_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(STABILITY_EVENT, 1000)  # every 1 second

    spawn_timer = 0  # ms until next spawn
    next_spawn_interval = random.randint(1000, 2000)

    running = True
    while running:
        dt = clock.tick(FPS)

        # ---- Events ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and not game_active:
                    # Restart
                    balance_value = 0
                    stable_timer = 0
                    game_active = True
                    won = False
                    catcher = Catcher()
                    emotions.clear()
                    floating_texts.clear()
                    spawn_timer = 0
                    next_spawn_interval = random.randint(1000, 2000)

            elif event.type == STABILITY_EVENT and game_active:
                if -5 <= balance_value <= 5:
                    stable_timer += 1
                else:
                    stable_timer = 0

        # ---- Update ----
        if game_active:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                catcher.move(-Catcher.SPEED)
            if keys[pygame.K_RIGHT]:
                catcher.move(Catcher.SPEED)

            # Spawn logic
            spawn_timer += dt
            if spawn_timer >= next_spawn_interval:
                spawn_timer = 0
                next_spawn_interval = random.randint(1000, 2000)
                emo_def = random.choice(EMOTIONS)
                emotions.append(FallingEmotion(emo_def))

            # Move emotions
            for emo in emotions:
                emo.update()

            # Collision detection
            caught_indices = []
            for i, emo in enumerate(emotions):
                if catcher.rect.colliderect(emo.rect):
                    caught_indices.append(i)
                    # Apply effect
                    if emo.emotion["special"] == "reset":
                        balance_value = 0
                    else:
                        balance_value += emo.emotion["effect"]
                    # Sound
                    pop_sound.play()
                    # Floating text
                    floating_texts.append(FloatingText(
                        emo.emotion["feedback"],
                        emo.x, emo.y,
                        emo.emotion["feedback_color"],
                    ))

            # Remove caught (reverse order to keep indices valid)
            for i in reversed(caught_indices):
                emotions.pop(i)

            # Remove off-screen
            emotions = [e for e in emotions if not e.is_off_screen()]

            # Floating text update
            for ft in floating_texts:
                ft.update()
            floating_texts = [ft for ft in floating_texts if not ft.is_expired()]

            # Win / Lose
            if stable_timer >= 30:
                game_active = False
                won = True
            elif balance_value > 50 or balance_value < -50:
                game_active = False
                won = False

        # ---- Draw ----
        screen.fill(SKY_BLUE)

        # Balance bar
        draw_balance_bar(screen, balance_value, stable_timer)

        # Falling emotions
        for emo in emotions:
            emo.draw(screen)

        # Catcher
        catcher.draw(screen)

        # Floating texts
        for ft in floating_texts:
            ft.draw(screen)

        # Win / Lose overlay
        if not game_active:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))

            if won:
                msg = font_large.render("\U0001F3C6 Balanced Soul! You Win!", True, (255, 215, 0))
            else:
                msg = font_large.render("\U0001F4A5 Emotion Overload! Game Over!", True, RED)
            msg_rect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            screen.blit(msg, msg_rect)

            hint = font_medium.render("Press R to Restart  or  ESC to Quit", True, WHITE)
            hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
            screen.blit(hint, hint_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
