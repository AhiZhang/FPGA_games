"""HDMI Flappy.

Any button flaps. Game over: BTN0 menu, other restart.
"""
from __future__ import annotations

import random
import time

from core.constants import HEIGHT, WIDTH
from core.gfx import blit_text, fill_rect

HEADER = 80
BIRD_X = 280
BIRD_W = 36
BIRD_H = 28
PIPE_W = 78
GAP = 168
GROUND_H = 54

C_BG = (18, 28, 48)
C_PANEL = (18, 28, 44)
C_SKY = (28, 46, 78)
C_TEXT = (236, 240, 245)
C_MUTED = (160, 178, 198)
C_TITLE = (244, 211, 94)
C_OVER = (232, 80, 80)
C_BIRD = (244, 211, 94)
C_BIRD_BEAK = (240, 150, 60)
C_PIPE = (80, 190, 90)
C_PIPE_DARK = (40, 120, 60)
C_GROUND = (70, 52, 36)
C_GRASS = (90, 170, 70)


class FlappyGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.y = 320.0
        self.vy = 0.0
        self.alive = True
        self.started = False
        self.score = 0
        self.pipes = []
        self._spawn_t = 0.0

    def flap(self):
        if not self.alive:
            return
        if not self.started:
            self.started = True
            self._spawn_t = 0.0
        self.vy = -430.0

    def _spawn_pipe(self):
        gap_y = random.randint(HEADER + 90, HEIGHT - GROUND_H - GAP - 50)
        self.pipes.append({"x": float(WIDTH + 20), "gap_y": gap_y, "scored": False})

    def step(self, dt):
        if not self.alive or not self.started:
            return False
        dt = min(dt, 0.04)
        self.vy += 1450.0 * dt
        self.y += self.vy * dt
        self._spawn_t += dt
        if self._spawn_t >= 1.45:
            self._spawn_t = 0.0
            self._spawn_pipe()
        speed = 250.0 + min(120.0, self.score * 6)
        for p in self.pipes:
            p["x"] -= speed * dt
        self.pipes = [p for p in self.pipes if p["x"] > -PIPE_W]

        bird_top = self.y
        bird_bot = self.y + BIRD_H
        if bird_top < HEADER + 8 or bird_bot > HEIGHT - GROUND_H:
            self.alive = False
            return True

        bx0, bx1 = BIRD_X, BIRD_X + BIRD_W
        for p in self.pipes:
            px0, px1 = p["x"], p["x"] + PIPE_W
            gap0, gap1 = p["gap_y"], p["gap_y"] + GAP
            if bx1 > px0 and bx0 < px1:
                if bird_top < gap0 or bird_bot > gap1:
                    self.alive = False
                    return True
            if not p["scored"] and px1 < bx0:
                p["scored"] = True
                self.score += 1
        return True


class FlappyScene:
    tick_s = 0.016

    def __init__(self):
        self.game = FlappyGame()
        self._exit_menu = False
        self._last = time.time()

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
        self.game.flap()

    def wants_menu(self):
        return self._exit_menu

    def needs_tick(self):
        return self.game.started and self.game.alive

    def tick(self):
        now = time.time()
        dt = now - self._last
        self._last = now
        return self.game.step(dt)

    def draw(self, canvas):
        g = self.game
        canvas[:] = C_SKY
        fill_rect(canvas, 0, 0, WIDTH, HEADER, C_PANEL)
        blit_text(canvas, 24, 16, "FLAPPY", C_TITLE, scale=6, gap=1)
        blit_text(canvas, 520, 22, "SCORE:%d" % g.score, C_TEXT, scale=4, gap=1)
        fill_rect(canvas, 0, HEIGHT - GROUND_H, WIDTH, HEIGHT, C_GROUND)
        fill_rect(canvas, 0, HEIGHT - GROUND_H, WIDTH, HEIGHT - GROUND_H + 10, C_GRASS)

        for p in g.pipes:
            x0 = int(p["x"])
            x1 = x0 + PIPE_W
            fill_rect(canvas, x0, HEADER, x1, int(p["gap_y"]), C_PIPE)
            fill_rect(canvas, x0 - 6, int(p["gap_y"]) - 18, x1 + 6, int(p["gap_y"]), C_PIPE_DARK)
            fill_rect(canvas, x0, int(p["gap_y"] + GAP), x1, HEIGHT - GROUND_H, C_PIPE)
            fill_rect(canvas, x0 - 6, int(p["gap_y"] + GAP), x1 + 6, int(p["gap_y"] + GAP) + 18, C_PIPE_DARK)

        by = int(g.y)
        fill_rect(canvas, BIRD_X, by, BIRD_X + BIRD_W, by + BIRD_H, C_BIRD)
        fill_rect(canvas, BIRD_X + BIRD_W - 8, by + 10, BIRD_X + BIRD_W + 10, by + 18, C_BIRD_BEAK)
        fill_rect(canvas, BIRD_X + 8, by + 8, BIRD_X + 16, by + 16, (20, 24, 32))
        blit_text(canvas, 40, HEIGHT - 36, "ANY BTN FLAP", C_MUTED, scale=2, gap=1)

        if not g.started and g.alive:
            fill_rect(canvas, 250, 240, 1030, 480, (10, 14, 28))
            fill_rect(canvas, 258, 248, 1022, 472, (20, 28, 44))
            blit_text(canvas, 360, 280, "PRESS TO FLAP", C_TITLE, scale=5, gap=2)
            blit_text(canvas, 300, 380, "BTN0 MENU AFTER GAME OVER", C_TEXT, scale=3, gap=1)
        elif not g.alive:
            fill_rect(canvas, 250, 240, 1030, 480, (10, 14, 28))
            fill_rect(canvas, 258, 248, 1022, 472, (28, 20, 20))
            blit_text(canvas, 360, 280, "GAME OVER", C_OVER, scale=7, gap=2)
            blit_text(canvas, 240, 380, "BTN0 MENU   OTHER RESTART", C_TEXT, scale=3, gap=1)
