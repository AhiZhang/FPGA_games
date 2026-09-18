"""HDMI Breakout.

BTN0 left, BTN3 right (hold to slide). BTN2/BTN1 launch the ball.
Game over: BTN0 menu, other buttons restart.
"""
from __future__ import annotations

import math
import random
import time

from core.constants import HEIGHT, WIDTH
from core.gfx import blit_text, fill_rect

HEADER = 80
PADDLE_W = 168
PADDLE_H = 18
PADDLE_Y = 640
BALL_R = 10
BRICK_COLS = 10
BRICK_ROWS = 5
BRICK_GAP = 8
BRICK_H = 28
FIELD_X = 40
FIELD_W = WIDTH - 80

C_BG = (8, 12, 24)
C_PANEL = (18, 28, 44)
C_TEXT = (236, 240, 245)
C_MUTED = (160, 178, 198)
C_TITLE = (244, 211, 94)
C_OVER = (232, 80, 80)
C_PADDLE = (80, 180, 255)
C_BALL = (255, 240, 220)
C_WALL = (40, 56, 84)
ROW_COLORS = (
    (232, 80, 80),
    (240, 150, 60),
    (244, 211, 94),
    (80, 200, 90),
    (70, 120, 230),
)


class BreakoutGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.paddle_x = (WIDTH - PADDLE_W) / 2
        self.ball_x = WIDTH / 2
        self.ball_y = PADDLE_Y - BALL_R - 2
        self.vx = 0.0
        self.vy = 0.0
        self.stuck = True
        self.alive = True
        self.started = False
        self.won = False
        self.score = 0
        self.lives = 3
        self.bricks = self._make_bricks()

    def _make_bricks(self):
        bricks = []
        brick_w = (FIELD_W - BRICK_GAP * (BRICK_COLS + 1)) // BRICK_COLS
        top = HEADER + 36
        for r in range(BRICK_ROWS):
            for c in range(BRICK_COLS):
                x = FIELD_X + BRICK_GAP + c * (brick_w + BRICK_GAP)
                y = top + r * (BRICK_H + BRICK_GAP)
                bricks.append(
                    {"x": x, "y": y, "w": brick_w, "h": BRICK_H, "color": ROW_COLORS[r]}
                )
        return bricks

    def launch(self):
        if not self.alive or not self.stuck:
            return
        self.stuck = False
        ang = random.uniform(-0.6, 0.6)
        speed = 420.0
        self.vx = speed * math.sin(ang)
        self.vy = -speed * math.cos(ang)

    def move_paddle(self, dx):
        self.paddle_x = max(FIELD_X, min(FIELD_X + FIELD_W - PADDLE_W, self.paddle_x + dx))
        if self.stuck:
            self.ball_x = self.paddle_x + PADDLE_W / 2

    def step(self, dt):
        if not self.alive or not self.started or self.stuck:
            return False
        dt = min(dt, 0.04)
        self.ball_x += self.vx * dt
        self.ball_y += self.vy * dt
        left, right = FIELD_X + BALL_R, FIELD_X + FIELD_W - BALL_R
        if self.ball_x < left:
            self.ball_x = left
            self.vx = abs(self.vx)
        elif self.ball_x > right:
            self.ball_x = right
            self.vx = -abs(self.vx)
        if self.ball_y < HEADER + BALL_R + 8:
            self.ball_y = HEADER + BALL_R + 8
            self.vy = abs(self.vy)

        px0, px1 = self.paddle_x, self.paddle_x + PADDLE_W
        if (
            self.vy > 0
            and PADDLE_Y - BALL_R <= self.ball_y <= PADDLE_Y + PADDLE_H
            and px0 - BALL_R <= self.ball_x <= px1 + BALL_R
        ):
            self.ball_y = PADDLE_Y - BALL_R
            hit = (self.ball_x - (px0 + PADDLE_W / 2)) / (PADDLE_W / 2)
            hit = max(-1.0, min(1.0, hit))
            speed = min(620.0, math.hypot(self.vx, self.vy) + 12)
            ang = hit * 1.05
            self.vx = speed * math.sin(ang)
            self.vy = -speed * math.cos(ang)

        hit_i = None
        for i, b in enumerate(self.bricks):
            if (
                b["x"] - BALL_R <= self.ball_x <= b["x"] + b["w"] + BALL_R
                and b["y"] - BALL_R <= self.ball_y <= b["y"] + b["h"] + BALL_R
            ):
                hit_i = i
                break
        if hit_i is not None:
            b = self.bricks.pop(hit_i)
            self.score += 10
            cx, cy = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
            if abs(self.ball_x - cx) * b["h"] > abs(self.ball_y - cy) * b["w"]:
                self.vx = -self.vx
            else:
                self.vy = -self.vy
            if not self.bricks:
                self.won = True
                self.alive = False
                return True

        if self.ball_y > HEIGHT + 20:
            self.lives -= 1
            if self.lives <= 0:
                self.alive = False
            else:
                self.stuck = True
                self.ball_x = self.paddle_x + PADDLE_W / 2
                self.ball_y = PADDLE_Y - BALL_R - 2
                self.vx = self.vy = 0.0
        return True


class BreakoutScene:
    tick_s = 0.016

    def __init__(self):
        self.game = BreakoutGame()
        self._exit_menu = False
        self._last = time.time()
        self._last_held = time.time()

    def handle_buttons(self, edges):
        if not edges:
            return
        if not self.game.alive:
            if 0 in edges:
                self._exit_menu = True
                return
            self.game.reset()
            self._last = time.time()
            return
        if not self.game.started:
            self.game.started = True
            return
        if 1 in edges or 2 in edges:
            self.game.launch()

    def handle_held(self, stable, now):
        if not self.game.started or not self.game.alive:
            self._last_held = now
            return False
        dt = min(0.04, max(0.0, now - self._last_held))
        self._last_held = now
        dx = 0.0
        if stable[0]:
            dx -= 640.0 * dt
        if stable[3]:
            dx += 640.0 * dt
        if dx == 0.0:
            return False
        self.game.move_paddle(dx)
        return True

    def wants_menu(self):
        return self._exit_menu

    def needs_tick(self):
        return self.game.started and self.game.alive and not self.game.stuck

    def tick(self):
        now = time.time()
        dt = now - self._last
        self._last = now
        return self.game.step(dt)

    def draw(self, canvas):
        g = self.game
        canvas[:] = C_BG
        fill_rect(canvas, 0, 0, WIDTH, HEADER, C_PANEL)
        blit_text(canvas, 24, 16, "BREAKOUT", C_TITLE, scale=6, gap=1)
        blit_text(canvas, 520, 22, "SCORE:%d" % g.score, C_TEXT, scale=3, gap=1)
        blit_text(canvas, 900, 22, "LIVES:%d" % g.lives, C_MUTED, scale=3, gap=1)
        fill_rect(canvas, FIELD_X, HEADER, FIELD_X + 6, HEIGHT, C_WALL)
        fill_rect(canvas, FIELD_X + FIELD_W - 6, HEADER, FIELD_X + FIELD_W, HEIGHT, C_WALL)
        fill_rect(canvas, FIELD_X, HEADER, FIELD_X + FIELD_W, HEADER + 8, C_WALL)

        for b in g.bricks:
            fill_rect(canvas, b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"], b["color"])

        fill_rect(
            canvas,
            int(g.paddle_x),
            PADDLE_Y,
            int(g.paddle_x + PADDLE_W),
            PADDLE_Y + PADDLE_H,
            C_PADDLE,
        )
        fill_rect(
            canvas,
            int(g.ball_x - BALL_R),
            int(g.ball_y - BALL_R),
            int(g.ball_x + BALL_R),
            int(g.ball_y + BALL_R),
            C_BALL,
        )
        blit_text(canvas, 40, HEIGHT - 40, "BTN0 L  BTN3 R  BTN2/1 LAUNCH", C_MUTED, scale=2, gap=1)

        if not g.started and g.alive:
            fill_rect(canvas, 250, 260, 1030, 500, (10, 14, 28))
            fill_rect(canvas, 258, 268, 1022, 492, (20, 28, 44))
            blit_text(canvas, 330, 300, "PRESS ANY BTN", C_TITLE, scale=6, gap=2)
            blit_text(canvas, 300, 400, "BTN0 MENU AFTER GAME OVER", C_TEXT, scale=3, gap=1)
        elif not g.alive:
            fill_rect(canvas, 250, 260, 1030, 500, (10, 14, 28))
            fill_rect(canvas, 258, 268, 1022, 492, (28, 20, 20))
            title = "YOU WIN" if g.won else "GAME OVER"
            blit_text(canvas, 360, 300, title, C_TITLE if g.won else C_OVER, scale=7, gap=2)
            blit_text(canvas, 240, 400, "BTN0 MENU   OTHER RESTART", C_TEXT, scale=3, gap=1)
