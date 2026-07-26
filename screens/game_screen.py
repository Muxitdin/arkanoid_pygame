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


def _start_game(level: int) -> tuple[Paddle, list[Ball], list[Brick], list[Bonus], int]:
    """Create a fresh game state for the selected level."""
    bricks, _, _ = load_level(level)
    return (
        Paddle(),
        [Ball(cfg.WIDTH // 2, cfg.HEIGHT - 40)],
        bricks,
        [],
        cfg.STARTING_LIVES,
    )


def run(screen: pygame.Surface, clock: pygame.time.Clock, level: int) -> None:
    """Run one playable Arkanoid level."""
    paddle, balls, bricks, bonuses, lives = _start_game(level)
    font = pygame.font.Font(None, 20)
    game_over_font = pygame.font.Font(None, 48)
    running = True
    game_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                paddle, balls, bricks, bonuses, lives = _start_game(level)
                game_over = False

        if not game_over:
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

            # With multiball, a life is lost only when the final ball is missed.
            if not balls:
                lives -= 1
                if lives == 0:
                    game_over = True
                else:
                    balls.append(Ball(paddle.rect.centerx, paddle.rect.top - cfg.BALL_RADIUS))

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

        lives_label = font.render(f"Lives: {lives}", True, cfg.WHITE)
        screen.blit(lives_label, (10, 10))
        if game_over:
            message = game_over_font.render("Game Over", True, cfg.RED)
            replay = font.render("Press Space to replay", True, cfg.WHITE)
            screen.blit(message, message.get_rect(center=(cfg.WIDTH // 2, cfg.HEIGHT // 2 - 16)))
            screen.blit(replay, replay.get_rect(center=(cfg.WIDTH // 2, cfg.HEIGHT // 2 + 24)))
        pygame.display.flip()
        clock.tick(cfg.FPS)
