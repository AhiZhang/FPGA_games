"""PYNQ-Z2 HDMI Snake scene.

Buttons:
    BTN0 left, BTN1 down, BTN2 up, BTN3 right
    GAME OVER: BTN0 back to menu, other buttons restart
"""
from __future__ import annotations

import random

import numpy as np

from core.constants import HEIGHT, WIDTH
from core.gfx import blit_text, fill_rect

CELL = 32
HEADER = 80
COLS = WIDTH // CELL
ROWS = (HEIGHT - HEADER) // CELL
TICK_S = 0.16

C_BG = (8, 12, 24)
C_PANEL = (18, 28, 44)
C_GRID = (28, 36, 52)
C_BORDER = (80, 140, 200)
C_SNAKE = (46, 196, 74)
C_HEAD = (90, 255, 120)
C_EYE = (16, 20, 28)
C_FOOD = (232, 64, 72)
C_FOOD_HI = (255, 170, 140)
C_TEXT = (236, 240, 245)
C_MUTED = (160, 178, 198)
C_OVER = (232, 80, 80)
C_TITLE = (244, 211, 94)
C_PLAY = (12, 18, 30)

DIRS = {
    0: (-1, 0),
    1: (0, 1),
    2: (0, -1),
    3: (1, 0),
}


def cell_rect(c, r, inset=2):
    x0 = c * CELL + inset
    y0 = HEADER + r * CELL + inset
    x1 = (c + 1) * CELL - inset
    y1 = HEADER + (r + 1) * CELL - inset
    return x0, y0, x1, y1


class SnakeGame:
    def __init__(self):
        self.reset()

    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx - 2, cy), (cx - 1, cy), (cx, cy)]
        self.direction = (1, 0)
        self.pending = None
        self.alive = True
        self.started = False
        self.score = 0
        self.food = self._place_food()
        self.ticks = 0

    def _place_food(self):
        occupied = set(self.snake)
        free = [(c, r) for c in range(COLS) for r in range(ROWS) if (c, r) not in occupied]
        if not free:
            return None
        return random.choice(free)

    def queue_dir(self, dxy):
        if not self.alive:
            return
        if not self.started:
            dx, dy = dxy
            cx, cy = self.direction
            if not (dx == -cx and dy == -cy):
                self.direction = (dx, dy)
            self.started = True
            self.pending = None
            return
        if self.pending is not None:
            return
        dx, dy = dxy
        cx, cy = self.direction
        if dx == -cx and dy == -cy:
            return
        if (dx, dy) == (cx, cy):
            return
        self.pending = (dx, dy)

    def step(self):
        if not self.alive or not self.started:
            return
        if self.pending is not None:
            self.direction = self.pending
            self.pending = None
        dx, dy = self.direction
        hx, hy = self.snake[-1]
        nx, ny = hx + dx, hy + dy
        if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
            self.alive = False
            return
        will_grow = self.food == (nx, ny)
        occupied = self.snake if will_grow else self.snake[1:]
        if (nx, ny) in occupied:
            self.alive = False
            return
        self.snake.append((nx, ny))
        if will_grow:
            self.score += 1
            self.food = self._place_food()
            if self.food is None:
                self.alive = False
        else:
            self.snake.pop(0)
        self.ticks += 1


def make_background():
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    img[:] = C_BG
    fill_rect(img, 0, 0, WIDTH, HEADER, C_PANEL)
    blit_text(img, 24, 16, "SNAKE", C_TITLE, scale=6, gap=1)
    blit_text(img, 24, 56, "BTN0 L  BTN1 D  BTN2 U  BTN3 R", C_MUTED, scale=2, gap=1)
    fill_rect(img, 0, HEADER, WIDTH, HEIGHT, C_PLAY)
    for c in range(COLS):
        x = c * CELL
        img[HEADER:HEIGHT, x : x + 1] = C_GRID
    for r in range(ROWS):
        y = HEADER + r * CELL
        img[y : y + 1, 0:WIDTH] = C_GRID
    img[HEADER : HEADER + 3, :] = C_BORDER
    img[-3:, :] = C_BORDER
    img[:, :3] = C_BORDER
    img[:, -3:] = C_BORDER
    return img


def draw_board(img, game, background):
    np.copyto(img, background)
    blit_text(img, 420, 24, "SCORE:%d" % game.score, C_TEXT, scale=4, gap=1)
    blit_text(img, 860, 24, "LEN:%d" % len(game.snake), C_MUTED, scale=4, gap=1)

    if game.food is not None:
        x0, y0, x1, y1 = cell_rect(*game.food, inset=6)
        fill_rect(img, x0, y0, x1, y1, C_FOOD)
        fill_rect(img, x0 + 4, y0 + 4, x0 + 12, y0 + 12, C_FOOD_HI)

    n = len(game.snake)
    for i, (c, r) in enumerate(game.snake):
        x0, y0, x1, y1 = cell_rect(c, r, inset=3)
        if i == n - 1:
            fill_rect(img, x0, y0, x1, y1, C_HEAD)
            dx, dy = game.direction
            mid_x = (x0 + x1) // 2
            mid_y = (y0 + y1) // 2
            if dx != 0:
                ey = mid_y - 5
                ex = mid_x + (6 if dx > 0 else -10)
                fill_rect(img, ex, ey, ex + 4, ey + 4, C_EYE)
                fill_rect(img, ex, ey + 10, ex + 4, ey + 14, C_EYE)
            else:
                ex = mid_x - 5
                ey = mid_y + (6 if dy > 0 else -10)
                fill_rect(img, ex, ey, ex + 4, ey + 4, C_EYE)
                fill_rect(img, ex + 10, ey, ex + 14, ey + 4, C_EYE)
        else:
            t = i / max(1, n - 1)
            body = (
                int(C_SNAKE[0] * (0.45 + 0.55 * t)),
                int(C_SNAKE[1] * (0.45 + 0.55 * t)),
                int(C_SNAKE[2] * (0.45 + 0.55 * t)),
            )
            fill_rect(img, x0, y0, x1, y1, body)

    if not game.started and game.alive:
        fill_rect(img, 250, 260, 1030, 500, (10, 14, 28))
        fill_rect(img, 258, 268, 1022, 492, (20, 28, 44))
        blit_text(img, 330, 300, "PRESS ANY BTN", C_TITLE, scale=6, gap=2)
        blit_text(img, 280, 400, "BTN0 MENU AFTER GAME OVER", C_TEXT, scale=3, gap=1)
    elif not game.alive:
        fill_rect(img, 250, 260, 1030, 500, (10, 14, 28))
        fill_rect(img, 258, 268, 1022, 492, (28, 20, 20))
        blit_text(img, 360, 300, "GAME OVER", C_OVER, scale=7, gap=2)
        blit_text(img, 240, 400, "BTN0 MENU   OTHER RESTART", C_TEXT, scale=3, gap=1)


class SnakeScene:
    tick_s = TICK_S

    def __init__(self):
        self.game = SnakeGame()
        self.background = make_background()
        self._exit_menu = False

    def handle_buttons(self, edges):
        if not edges:
            return
        if not self.game.alive:
            if 0 in edges:
                self._exit_menu = True
                return
            self.game.reset()
            return
        for i in edges:
            self.game.queue_dir(DIRS[i])

    def wants_menu(self):
        return self._exit_menu

    def tick(self):
        self.game.step()

    def needs_tick(self):
        return self.game.started and self.game.alive

    def draw(self, canvas):
        draw_board(canvas, self.game, self.background)
