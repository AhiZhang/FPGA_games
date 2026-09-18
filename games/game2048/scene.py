"""HDMI 2048.

BTN0 left, BTN1 down, BTN2 up, BTN3 right.
Game over: BTN0 menu, other buttons restart.
"""
from __future__ import annotations

import random

from core.constants import HEIGHT, WIDTH
from core.gfx import blit_text, fill_rect

N = 4
CELL = 118
GAP = 12
BOARD = N * CELL + (N + 1) * GAP
BOARD_X = (WIDTH - BOARD) // 2
BOARD_Y = 118

C_BG = (8, 12, 24)
C_PANEL = (18, 28, 44)
C_BOARD = (28, 34, 48)
C_TEXT = (236, 240, 245)
C_MUTED = (160, 178, 198)
C_TITLE = (244, 211, 94)
C_OVER = (232, 80, 80)
C_DARK = (40, 36, 32)

TILE_BG = {
    0: (36, 42, 56),
    2: (232, 224, 208),
    4: (236, 214, 176),
    8: (240, 164, 96),
    16: (236, 128, 72),
    32: (232, 96, 72),
    64: (220, 64, 48),
    128: (236, 204, 96),
    256: (236, 196, 64),
    512: (236, 188, 40),
    1024: (236, 176, 24),
    2048: (236, 160, 16),
}


def _tile_color(v):
    if v in TILE_BG:
        return TILE_BG[v]
    return (60, 48, 40)


def _slide_left(row):
    vals = [v for v in row if v]
    out = []
    gained = 0
    i = 0
    while i < len(vals):
        if i + 1 < len(vals) and vals[i] == vals[i + 1]:
            merged = vals[i] * 2
            out.append(merged)
            gained += merged
            i += 2
        else:
            out.append(vals[i])
            i += 1
    out.extend([0] * (N - len(out)))
    return out, gained


class Game2048:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = [[0] * N for _ in range(N)]
        self.score = 0
        self.alive = True
        self.started = False
        self.won = False

    def _empties(self):
        return [(r, c) for r in range(N) for c in range(N) if self.grid[r][c] == 0]

    def _spawn(self):
        spots = self._empties()
        if not spots:
            return
        r, c = random.choice(spots)
        self.grid[r][c] = 4 if random.random() < 0.1 else 2

    def start(self):
        if self.started:
            return
        self.started = True
        self._spawn()
        self._spawn()

    def _set_rows(self, rows):
        self.grid = [list(r) for r in rows]

    def move(self, direction):
        if not self.alive or not self.started:
            return False
        old = [row[:] for row in self.grid]
        gained = 0
        if direction == "L":
            rows = []
            for row in self.grid:
                nr, g = _slide_left(row)
                rows.append(nr)
                gained += g
            self._set_rows(rows)
        elif direction == "R":
            rows = []
            for row in self.grid:
                nr, g = _slide_left(list(reversed(row)))
                rows.append(list(reversed(nr)))
                gained += g
            self._set_rows(rows)
        elif direction == "U":
            cols = []
            for c in range(N):
                col = [self.grid[r][c] for r in range(N)]
                nc, g = _slide_left(col)
                cols.append(nc)
                gained += g
            self.grid = [[cols[c][r] for c in range(N)] for r in range(N)]
        elif direction == "D":
            cols = []
            for c in range(N):
                col = [self.grid[r][c] for r in range(N)]
                nc, g = _slide_left(list(reversed(col)))
                cols.append(list(reversed(nc)))
                gained += g
            self.grid = [[cols[c][r] for c in range(N)] for r in range(N)]
        if self.grid == old:
            return False
        self.score += gained
        if any(v >= 2048 for row in self.grid for v in row):
            self.won = True
        self._spawn()
        if not self._empties() and not self._can_move():
            self.alive = False
        return True

    def _can_move(self):
        for r in range(N):
            for c in range(N):
                v = self.grid[r][c]
                if v == 0:
                    return True
                if c + 1 < N and self.grid[r][c + 1] == v:
                    return True
                if r + 1 < N and self.grid[r + 1][c] == v:
                    return True
        return False


class Game2048Scene:
    tick_s = 0.2

    def __init__(self):
        self.game = Game2048()
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
        if not self.game.started:
            self.game.start()
            if 0 in edges:
                self.game.move("L")
            elif 1 in edges:
                self.game.move("D")
            elif 2 in edges:
                self.game.move("U")
            elif 3 in edges:
                self.game.move("R")
            return
        for i in edges:
            if i == 0:
                self.game.move("L")
            elif i == 1:
                self.game.move("D")
            elif i == 2:
                self.game.move("U")
            elif i == 3:
                self.game.move("R")

    def wants_menu(self):
        return self._exit_menu

    def needs_tick(self):
        return False

    def tick(self):
        return False

    def draw(self, canvas):
        g = self.game
        canvas[:] = C_BG
        fill_rect(canvas, 0, 0, WIDTH, 80, C_PANEL)
        blit_text(canvas, 24, 16, "2048", C_TITLE, scale=6, gap=1)
        blit_text(canvas, 420, 22, "SCORE:%d" % g.score, C_TEXT, scale=4, gap=1)
        if g.won:
            blit_text(canvas, 900, 22, "2048!", C_TITLE, scale=4, gap=1)

        fill_rect(canvas, BOARD_X, BOARD_Y, BOARD_X + BOARD, BOARD_Y + BOARD, C_BOARD)
        for r in range(N):
            for c in range(N):
                v = g.grid[r][c]
                x0 = BOARD_X + GAP + c * (CELL + GAP)
                y0 = BOARD_Y + GAP + r * (CELL + GAP)
                fill_rect(canvas, x0, y0, x0 + CELL, y0 + CELL, _tile_color(v))
                if v:
                    label = str(v)
                    scale = 4 if v < 1000 else 3
                    tw = len(label) * (5 + 1) * scale
                    tx = x0 + (CELL - tw) // 2
                    ty = y0 + (CELL - 7 * scale) // 2
                    color = C_DARK if v <= 4 else C_TEXT
                    blit_text(canvas, tx, ty, label, color, scale=scale, gap=1)

        blit_text(canvas, 40, HEIGHT - 40, "BTN0 L  BTN1 D  BTN2 U  BTN3 R", C_MUTED, scale=2, gap=1)

        if not g.started:
            fill_rect(canvas, 250, 260, 1030, 500, (10, 14, 28))
            fill_rect(canvas, 258, 268, 1022, 492, (20, 28, 44))
            blit_text(canvas, 330, 300, "PRESS ANY BTN", C_TITLE, scale=6, gap=2)
            blit_text(canvas, 300, 400, "BTN0 MENU AFTER GAME OVER", C_TEXT, scale=3, gap=1)
        elif not g.alive:
            fill_rect(canvas, 250, 260, 1030, 500, (10, 14, 28))
            fill_rect(canvas, 258, 268, 1022, 492, (28, 20, 20))
            blit_text(canvas, 360, 300, "GAME OVER", C_OVER, scale=7, gap=2)
            blit_text(canvas, 240, 400, "BTN0 MENU   OTHER RESTART", C_TEXT, scale=3, gap=1)
