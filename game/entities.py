import math

import pygame

import settings as cfg


# Each entry is the internal name, the one-character icon, and its display color.
# Keeping this catalogue beside the game entities makes it the single source of
# truth for both bonus creation and drawing.
POWER_UPS = {
    "extend": ("E", cfg.CYAN),
    "multiball": ("M", cfg.MAGENTA),
    "laser": ("L", cfg.ORANGE),
    "extra_life": ("+", cfg.GREEN),
    "shrink": ("S", cfg.RED),
    "speed_up": ("U", cfg.YELLOW),
    "speed_down": ("D", cfg.GRAY),
}

class Paddle:
    """ Our main player, Paddle, moves only horizontally. """

    def __init__(self) -> None:
        self.rect = pygame.Rect(0, 0, cfg.PADDLE_WIDTH, cfg.PADDLE_HEIGHT)
        self.rect.midbottom = (cfg.WIDTH // 2, cfg.HEIGHT - 20)
        self.speed = cfg.PADDLE_SPEED
        self.vx = 0
        self.extended = False
        self.laser = False

    def move(self, keys: pygame.key.ScancodeWrapper):
        """ Moves the Paddle if the key is pressed. """
        self.vx = 0
        if keys[pygame.K_LEFT]:
            self.vx = -self.speed
        elif keys[pygame.K_RIGHT]:
            self.vx = self.speed
        
        self.rect.x += self.vx

        # Restrict the Paddle's movement
        if self.rect.left < cfg.FIELD_LEFT:
            self.rect.left = cfg.FIELD_LEFT
        if self.rect.right > cfg.FIELD_RIGHT:
            self.rect.right = cfg.FIELD_RIGHT

    def draw(self, screen: pygame.Surface) -> None:
        """ Renders the Paddle on the screen. """
        pygame.draw.rect(screen, cfg.PADDLE_COLOR, self.rect, border_radius=5)

    def resize(self, width: int) -> None:
        """Change width while keeping the paddle centred and inside the field."""
        center_x = self.rect.centerx
        self.rect.width = width
        self.rect.centerx = center_x
        self.rect.left = max(cfg.FIELD_LEFT, self.rect.left)
        self.rect.right = min(cfg.FIELD_RIGHT, self.rect.right)


class Brick:
    """
        Class for Game's brick.

        HP = -1: Level Boundary
        HP = 0: Indestructable
        HP = 1, 2: One / Two hit
    """
    
    def __init__(self, col: int, row: int, hp: int) -> None:
        self.hp = hp
        self.color = cfg.BRICK_COLORS[hp]
        self.rect = pygame.Rect(
            cfg.FIELD_LEFT + col * cfg.BRICK_WIDTH,
            cfg.TOP_OFFSET + row * cfg.BRICK_HEIGHT,
            cfg.BRICK_WIDTH,
            cfg.BRICK_HEIGHT,
        )

    def draw(self, screen: pygame.Surface) -> None:
        """ Renders a Brick in a certain row and col. """
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, cfg.DARK_GRAY, self.rect, 2)
    
    def hit(self) -> None:
        """ Handles the Brick Hit. """
        if self.hp > 0:
            self.hp -= 1
            if self.hp > 0:
                self.color = cfg.BRICK_COLORS[self.hp]
                return
        return

class Ball:
    """ Ball Actor class. """

    def __init__(self, x: int, y: int) -> None:
        self.radius = cfg.BALL_RADIUS
        self.rect = pygame.Rect(
            x - self.radius,
            y - self.radius,
            2 * self.radius,
            2 * self.radius,
        )
        self.vx = cfg.BALL_SPEED_X
        self.vy = cfg.BALL_SPEED_Y

    def update(self) -> None:
        """ Updates the Ball's position for the each frame. """
        self.rect.x += self.vx
        self.rect.y += self.vy

    def draw(self, screen: pygame.surface) -> None:
        """ Renders the Ball. """
        colour = cfg.BALL_COLOR
        pygame.draw.circle(screen, colour, self.rect.center, self.radius)

    def change_speed(self, factor: float) -> None:
        """Scale both velocity components, retaining their direction."""
        def scaled(value: float) -> int:
            magnitude = max(2, min(10, round(abs(value) * factor)))
            return int(math.copysign(magnitude, value))

        self.vx = scaled(self.vx)
        self.vy = scaled(self.vy)


class Bonus:
    """A falling collectible created when a brick is destroyed."""

    WIDTH, HEIGHT = 26, 18

    def __init__(self, bonus_type: str, center: tuple[int, int]) -> None:
        self.type = bonus_type
        self.icon, self.color = POWER_UPS[bonus_type]
        self.rect = pygame.Rect(0, 0, self.WIDTH, self.HEIGHT)
        self.rect.center = center

    def update(self) -> None:
        self.rect.y += cfg.BONUS_FALL_SPEED

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(screen, self.color, self.rect, border_radius=4)
        label = font.render(self.icon, True, cfg.BLACK)
        screen.blit(label, label.get_rect(center=self.rect.center))
