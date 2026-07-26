import random

import pygame

import settings as cfg
from game.entities import Ball, Bonus, Brick, POWER_UPS, Paddle
from game.level import load_level


def _bounce_off_rect(ball: Ball, rect: pygame.Rect) -> None:
    """Resolve a ball collision by bouncing off the closest rectangle edge."""
    overlaps = {
        "left": ball.rect.right - rect.left,
        "right": rect.right - ball.rect.left,
        "top": ball.rect.bottom - rect.top,
        "bottom": rect.bottom - ball.rect.top,
    }
    edge = min(overlaps, key=overlaps.get)
    if edge == "top" and ball.vy > 0:
        ball.rect.bottom = rect.top
        ball.vy *= -1
    elif edge == "bottom" and ball.vy < 0:
        ball.rect.top = rect.bottom
        ball.vy *= -1
    elif edge == "left" and ball.vx > 0:
        ball.rect.right = rect.left
        ball.vx *= -1
    elif edge == "right" and ball.vx < 0:
        ball.rect.left = rect.right
        ball.vx *= -1


def ApplyBonus(bonus_type: str, paddle: Paddle, balls: list[Ball]) -> None:
    """Apply a collected power-up to the player or every active ball."""
    if bonus_type == "extend":
        paddle.resize(min(cfg.FIELD_RIGHT - cfg.FIELD_LEFT, paddle.rect.width + 30))
    elif bonus_type == "shrink":
        paddle.resize(max(50, paddle.rect.width - 30))
    elif bonus_type == "speed_up":
        for ball in balls:
            ball.change_speed(1.25)
    elif bonus_type == "speed_down":
        for ball in balls:
            ball.change_speed(0.75)
    elif bonus_type == "multiball" and balls:
        source = balls[0]
        extra = Ball(source.rect.centerx, source.rect.centery)
        extra.vx, extra.vy = -source.vx, source.vy
        balls.append(extra)
    # Laser and extra-life are retained in the catalogue for future gameplay.
    elif bonus_type == "laser":
        paddle.laser = True


def _handle_ball_vs_bricks(ball: Ball, bricks: list[Brick], bonuses: list[Bonus]) -> None:
    for brick in bricks[:]:
        if not ball.rect.colliderect(brick.rect):
            continue
        _bounce_off_rect(ball, brick.rect)
        if brick.hp <= 0:
            continue
        brick.hit()
        if brick.hp == 0:
            bricks.remove(brick)
            if random.random() < cfg.BONUS_PROBABILITY:
                bonuses.append(Bonus(random.choice(tuple(POWER_UPS)), brick.rect.center))
        return


def run(screen: pygame.Surface, clock: pygame.time.Clock, level: int) -> None:
    """Run one playable Arkanoid level."""
    paddle = Paddle()
    balls = [Ball(cfg.WIDTH // 2, cfg.HEIGHT - 40)]
    bricks, _, _ = load_level(level)
    bonuses: list[Bonus] = []
    font = pygame.font.Font(None, 20)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        paddle.move(pygame.key.get_pressed())
        for ball in balls[:]:
            _handle_ball_vs_bricks(ball, bricks, bonuses)
            if ball.rect.colliderect(paddle.rect) and ball.vy > 0:
                _bounce_off_rect(ball, paddle.rect)
                offset = (ball.rect.centerx - paddle.rect.centerx) / (paddle.rect.width / 2)
                ball.vx = round(max(-cfg.MAX_BALL_SPEED_X, min(cfg.MAX_BALL_SPEED_X, offset * cfg.MAX_BALL_SPEED_X)))
            ball.update()
            if ball.rect.top > cfg.HEIGHT:
                balls.remove(ball)

        for bonus in bonuses[:]:
            bonus.update()
            if bonus.rect.colliderect(paddle.rect):
                ApplyBonus(bonus.type, paddle, balls)
                bonuses.remove(bonus)
            elif bonus.rect.top > cfg.HEIGHT:
                bonuses.remove(bonus)

        screen.fill(cfg.BLACK)
        for brick in bricks:
            brick.draw(screen)
        for bonus in bonuses:
            bonus.draw(screen, font)
        paddle.draw(screen)
        for ball in balls:
            ball.draw(screen)
        pygame.display.flip()
        clock.tick(cfg.FPS)
