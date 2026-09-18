"""HDMI Tetris.

BTN0 left, BTN3 right, BTN2 rotate, BTN1 soft drop.
Each press moves one cell or rotates once; holding does not repeat.
Game over: BTN0 menu, other buttons restart.
"""
from __future__ import annotations

import random
import time

from core.constants import WIDTH
from core.gfx import blit_text, fill_rect

COLS = 10
ROWS = 20
CELL = 28
WELL_W = COLS * CELL
WELL_H = ROWS * CELL
WELL_X = 80
WELL_Y = 100

C_BG = (8, 12, 24)
C_PANEL = (18, 28, 44)
C_WELL = (10, 14, 22)
C_GRID = (32, 40, 56)
C_BORDER = (80, 140, 200)
C_TEXT = (236, 240, 245)
C_MUTED = (160, 178, 198)
C_TITLE = (244, 211, 94)
C_OVER = (232, 80, 80)
C_GHOST_A = 0.28

PIECES = {
    "I": (
        ((0, 1), (1, 1), (2, 1), (3, 1)),
        ((2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 2), (1, 2), (2, 2), (3, 2)),
        ((1, 0), (1, 1), (1, 2), (1, 3)),
    ),
    "J": (
        ((0, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (2, 2)),
        ((1, 0), (1, 1), (0, 2), (1, 2)),
    ),
    "L": (
        ((2, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (1, 1), (2, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
    "O": (
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
        ((1, 0), (2, 0), (1, 1), (2, 1)),
    ),
    "S": (
        ((1, 0), (2, 0), (0, 1), (1, 1)),
        ((1, 0), (1, 1), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (0, 2), (1, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "T": (
        ((1, 0), (0, 1), (1, 1), (2, 1)),
        ((1, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (2, 1), (1, 2)),
        ((1, 0), (0, 1), (1, 1), (1, 2)),
    ),
    "Z": (
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((2, 0), (1, 1), (2, 1), (1, 2)),
        ((0, 1), (1, 1), (1, 2), (2, 2)),
        ((1, 0), (0, 1), (1, 1), (0, 2)),
    ),
}

COLORS = {
    "I": (64, 210, 230),
    "J": (70, 120, 230),
    "L": (240, 150, 60),
    "O": (244, 211, 94),
    "S": (80, 200, 90),
    "T": (180, 100, 220),
    "Z": (232, 80, 80),
}

KICKS = ((0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0), (0, 1))
NAMES = tuple(PIECES.keys())
LINE_SCORE = (0, 100, 300, 500, 800)


def _mix(color, bg, a):
    return tuple(int(c * a + b * (1.0 - a)) for c, b in zip(color, bg))


class TetrisGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.bag = []
        self.next_kind = None
        self.kind = None
        self.rot = 0
        self.x = 3
        self.y = 0
        self.alive = True
        self.started = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self._fill_bag()
        self.next_kind = self.bag.pop()
        self._fill_bag()

    def _fill_bag(self):
        chunk = list(NAMES)
        random.shuffle(chunk)
        self.bag.extend(chunk)

    def gravity_s(self):
        return max(0.12, 0.72 - (self.level - 1) * 0.06)

    def _cells(self, kind=None, rot=None, x=None, y=None):
        kind = self.kind if kind is None else kind
        rot = self.rot if rot is None else rot
        x = self.x if x is None else x
        y = self.y if y is None else y
        return [(x + dx, y + dy) for dx, dy in PIECES[kind][rot]]

    def _collides(self, kind=None, rot=None, x=None, y=None):
        for cx, cy in self._cells(kind, rot, x, y):
            if cx < 0 or cx >= COLS or cy >= ROWS:
                return True
            if cy >= 0 and self.board[cy][cx]:
                return True
        return False

    def spawn(self):
        self.kind = self.next_kind
        self.next_kind = self.bag.pop()
        self._fill_bag()
        self.rot = 0
        self.x = 3
        self.y = 0
        if self._collides():
            self.alive = False
            self.kind = None

    def start(self):
        if self.started or not self.alive:
            return
        self.started = True
        self.spawn()

    def move(self, dx, dy):
        if not self.alive or not self.started or self.kind is None:
            return False
        nx, ny = self.x + dx, self.y + dy
        if self._collides(x=nx, y=ny):
            if dy > 0:
                self._lock()
                return True
            return False
        self.x, self.y = nx, ny
        if dy > 0:
            self.score += 1
        return True

    def rotate(self):
        if not self.alive or not self.started or self.kind is None:
            return False
        nxt = (self.rot + 1) % 4
        for kx, ky in KICKS:
            if not self._collides(rot=nxt, x=self.x + kx, y=self.y + ky):
                self.rot = nxt
                self.x += kx
                self.y += ky
                return True
        return False

    def gravity(self):
        if not self.alive or not self.started or self.kind is None:
            return False
        if not self._collides(y=self.y + 1):
            self.y += 1
            return True
        self._lock()
        return True

    def ghost_y(self):
        if self.kind is None:
            return self.y
        gy = self.y
        while not self._collides(y=gy + 1):
            gy += 1
        return gy

    def _lock(self):
        if self.kind is None:
            return
        for cx, cy in self._cells():
            if 0 <= cy < ROWS and 0 <= cx < COLS:
                self.board[cy][cx] = self.kind
        self.kind = None
        cleared = 0
        new_board = [row for row in self.board if not all(row)]
        cleared = ROWS - len(new_board)
        if cleared:
            self.board = [[None] * COLS for _ in range(cleared)] + new_board
            self.score += LINE_SCORE[cleared] * self.level
            self.lines += cleared
            self.level = self.lines // 10 + 1
        self.spawn()


class TetrisScene:
    tick_s = 0.05

    def __init__(self):
        self.game = TetrisGame()
        self._exit_menu = False
        self._last_grav = time.time()

    def handle_buttons(self, edges):
        now = time.time()
        if not edges:
            return
        if not self.game.alive:
            if 0 in edges:
                self._exit_menu = True
                return
            self.game.reset()
            self._last_grav = now
            return
        if not self.game.started:
            self.game.start()
            self._last_grav = now
            return
        # One cell / one rotation per press; holding must not slide extra cells.
        for i in edges:
            if i == 0:
                self.game.move(-1, 0)
            elif i == 3:
                self.game.move(1, 0)
            elif i == 1:
                self.game.move(0, 1)
                self._last_grav = now
            elif i == 2:
                self.game.rotate()

    def wants_menu(self):
        return self._exit_menu

    def needs_tick(self):
        return self.game.started and self.game.alive

    def tick(self):
        now = time.time()
        if now - self._last_grav >= self.game.gravity_s():
            self.game.gravity()
            self._last_grav = now
            return True
        return False

    def draw(self, canvas):
        canvas[:] = C_BG
        fill_rect(canvas, 0, 0, WIDTH, 80, C_PANEL)
        blit_text(canvas, 24, 16, "TETRIS", C_TITLE, scale=6, gap=1)
        blit_text(canvas, 420, 22, "SCORE:%d" % self.game.score, C_TEXT, scale=3, gap=1)
        blit_text(canvas, 820, 22, "LV:%d  LINES:%d" % (self.game.level, self.game.lines), C_MUTED, scale=3, gap=1)

        fill_rect(canvas, WELL_X - 4, WELL_Y - 4, WELL_X + WELL_W + 4, WELL_Y + WELL_H + 4, C_BORDER)
        fill_rect(canvas, WELL_X, WELL_Y, WELL_X + WELL_W, WELL_Y + WELL_H, C_WELL)
        for r in range(ROWS + 1):
            y = WELL_Y + r * CELL
            canvas[y : y + 1, WELL_X : WELL_X + WELL_W] = C_GRID
        for c in range(COLS + 1):
            x = WELL_X + c * CELL
            canvas[WELL_Y : WELL_Y + WELL_H, x : x + 1] = C_GRID

        for r in range(ROWS):
            for c in range(COLS):
                kind = self.game.board[r][c]
                if kind:
                    self._draw_cell(canvas, c, r, COLORS[kind])

        if self.game.kind is not None:
            gy = self.game.ghost_y()
            ghost = _mix(COLORS[self.game.kind], C_WELL, C_GHOST_A)
            if gy != self.game.y:
                for cx, cy in self.game._cells(y=gy):
                    if cy >= 0:
                        self._draw_cell(canvas, cx, cy, ghost, inset=4)
            for cx, cy in self.game._cells():
                if cy >= 0:
                    self._draw_cell(canvas, cx, cy, COLORS[self.game.kind])

        px, py = 460, 120
        fill_rect(canvas, px, py, px + 280, py + 220, C_PANEL)
        blit_text(canvas, px + 20, py + 16, "NEXT", C_MUTED, scale=3, gap=1)
        if self.game.next_kind:
            self._draw_preview(canvas, px + 70, py + 70, self.game.next_kind)

        blit_text(canvas, 460, 380, "BTN0 L   BTN3 R", C_MUTED, scale=3, gap=1)
        blit_text(canvas, 460, 430, "BTN2 ROT  BTN1 DROP", C_MUTED, scale=3, gap=1)

        if not self.game.started and self.game.alive:
            fill_rect(canvas, 250, 260, 1030, 500, (10, 14, 28))
            fill_rect(canvas, 258, 268, 1022, 492, (20, 28, 44))
            blit_text(canvas, 330, 300, "PRESS ANY BTN", C_TITLE, scale=6, gap=2)
            blit_text(canvas, 300, 400, "BTN0 MENU AFTER GAME OVER", C_TEXT, scale=3, gap=1)
        elif not self.game.alive:
            fill_rect(canvas, 250, 260, 1030, 500, (10, 14, 28))
            fill_rect(canvas, 258, 268, 1022, 492, (28, 20, 20))
            blit_text(canvas, 360, 300, "GAME OVER", C_OVER, scale=7, gap=2)
            blit_text(canvas, 240, 400, "BTN0 MENU   OTHER RESTART", C_TEXT, scale=3, gap=1)

    def _draw_cell(self, canvas, c, r, color, inset=2):
        x0 = WELL_X + c * CELL + inset
        y0 = WELL_Y + r * CELL + inset
        x1 = WELL_X + (c + 1) * CELL - inset
        y1 = WELL_Y + (r + 1) * CELL - inset
        fill_rect(canvas, x0, y0, x1, y1, color)

    def _draw_preview(self, canvas, x, y, kind):
        color = COLORS[kind]
        for dx, dy in PIECES[kind][0]:
            fill_rect(
                canvas,
                x + dx * CELL + 2,
                y + dy * CELL + 2,
                x + (dx + 1) * CELL - 2,
                y + (dy + 1) * CELL - 2,
                color,
            )
