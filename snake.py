#!/usr/bin/env python3
"""PYNQ-Z2 HDMI Snake. Run as root with the pynq venv.

Buttons (rising-edge, debounced, one direction change per tick):
    BTN0 left, BTN1 down, BTN2 up, BTN3 right
"""
from __future__ import annotations

import os
import random
import signal
import sys
import time

import numpy as np
from pynq.lib.video import PIXEL_RGB, VideoMode
from pynq.overlays.base import BaseOverlay

# Match the known-good HDMI clock demo on this board.
WIDTH, HEIGHT = 1280, 720
CELL = 32
HEADER = 80
COLS = WIDTH // CELL              # 40
ROWS = (HEIGHT - HEADER) // CELL  # 20

TICK_S = 0.16
POLL_S = 0.005
STABLE_N = 4  # ~20 ms debounce

# RGB
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
    0: (-1, 0),  # BTN0 left
    1: (0, 1),   # BTN1 down
    2: (0, -1),  # BTN2 up
    3: (1, 0),   # BTN3 right
}

FONT = {
    " ": [0x00, 0x00, 0x00, 0x00, 0x00],
    "0": [0x3E, 0x45, 0x49, 0x51, 0x3E],
    "1": [0x00, 0x21, 0x7F, 0x01, 0x00],
    "2": [0x21, 0x43, 0x45, 0x49, 0x31],
    "3": [0x42, 0x41, 0x51, 0x69, 0x46],
    "4": [0x0C, 0x14, 0x24, 0x7F, 0x04],
    "5": [0x72, 0x51, 0x51, 0x51, 0x4E],
    "6": [0x3E, 0x51, 0x51, 0x51, 0x0E],
    "7": [0x40, 0x47, 0x48, 0x50, 0x60],
    "8": [0x2E, 0x51, 0x51, 0x51, 0x2E],
    "9": [0x30, 0x49, 0x49, 0x49, 0x3E],
    "A": [0x3F, 0x48, 0x48, 0x48, 0x3F],
    "B": [0x7F, 0x49, 0x49, 0x49, 0x36],
    "C": [0x3E, 0x41, 0x41, 0x41, 0x22],
    "D": [0x7F, 0x41, 0x41, 0x41, 0x3E],
    "E": [0x7F, 0x49, 0x49, 0x49, 0x41],
    "F": [0x7F, 0x48, 0x48, 0x48, 0x40],
    "G": [0x3E, 0x41, 0x49, 0x49, 0x2E],
    "H": [0x7F, 0x08, 0x08, 0x08, 0x7F],
    "I": [0x00, 0x41, 0x7F, 0x41, 0x00],
    "K": [0x7F, 0x08, 0x14, 0x22, 0x41],
    "L": [0x7F, 0x01, 0x01, 0x01, 0x01],
    "M": [0x7F, 0x20, 0x18, 0x20, 0x7F],
    "N": [0x7F, 0x10, 0x08, 0x04, 0x7F],
    "O": [0x3E, 0x41, 0x41, 0x41, 0x3E],
    "P": [0x7F, 0x48, 0x48, 0x48, 0x30],
    "R": [0x7F, 0x48, 0x4C, 0x4A, 0x31],
    "S": [0x32, 0x49, 0x49, 0x49, 0x26],
    "T": [0x40, 0x40, 0x7F, 0x40, 0x40],
    "U": [0x7E, 0x01, 0x01, 0x01, 0x7E],
    "V": [0x7C, 0x02, 0x01, 0x02, 0x7C],
    "W": [0x7F, 0x02, 0x0C, 0x02, 0x7F],
    "Y": [0x60, 0x10, 0x0F, 0x10, 0x60],
    ":": [0x00, 0x36, 0x36, 0x00, 0x00],
    "-": [0x08, 0x08, 0x08, 0x08, 0x08],
    "!": [0x00, 0x00, 0x7D, 0x00, 0x00],
    "/": [0x03, 0x04, 0x08, 0x10, 0x60],
}


def log(msg: str) -> None:
    print(msg, flush=True)


def blit_text(img, x, y, text, color=C_TEXT, scale=3, gap=1):
    cx = x
    color = np.asarray(color, dtype=np.uint8)
    h, w = img.shape[:2]
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for col, bits in enumerate(glyph):
            for row in range(7):
                if bits & (1 << (6 - row)):
                    y0 = y + row * scale
                    x0 = cx + col * scale
                    y1 = min(y0 + scale, h)
                    x1 = min(x0 + scale, w)
                    if y1 > y0 and x1 > x0:
                        img[y0:y1, x0:x1] = color
        cx += (5 + gap) * scale


def fill_rect(img, x0, y0, x1, y1, color):
    h, w = img.shape[:2]
    xa, xb = max(0, int(x0)), min(w, int(x1))
    ya, yb = max(0, int(y0)), min(h, int(y1))
    if xb > xa and yb > ya:
        img[ya:yb, xa:xb] = color


def cell_rect(c, r, inset=2):
    x0 = c * CELL + inset
    y0 = HEADER + r * CELL + inset
    x1 = (c + 1) * CELL - inset
    y1 = HEADER + (r + 1) * CELL - inset
    return x0, y0, x1, y1


class Buttons:
    """Debounced rising-edge reader. Holding a key does not retrigger."""

    def __init__(self, gpio):
        self.gpio = gpio
        self._raw = [0, 0, 0, 0]
        self._stable = [0, 0, 0, 0]
        self._count = [0, 0, 0, 0]
        self._prev = [0, 0, 0, 0]

    def _read_raw(self):
        val = int(self.gpio.read()) & 0xF
        return [(val >> i) & 1 for i in range(4)]

    def poll(self):
        raw = self._read_raw()
        for i in range(4):
            if raw[i] == self._raw[i]:
                self._count[i] += 1
            else:
                self._raw[i] = raw[i]
                self._count[i] = 1
            if self._count[i] >= STABLE_N:
                self._stable[i] = self._raw[i]
        edges = []
        for i in range(4):
            if self._stable[i] and not self._prev[i]:
                edges.append(i)
            self._prev[i] = self._stable[i]
        return edges


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
        img[HEADER:HEIGHT, x:x + 1] = C_GRID
    for r in range(ROWS):
        y = HEADER + r * CELL
        img[y:y + 1, 0:WIDTH] = C_GRID
    img[HEADER:HEADER + 3, :] = C_BORDER
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
        blit_text(img, 360, 400, "BTN0 L  BTN3 R", C_TEXT, scale=3, gap=1)
    elif not game.alive:
        fill_rect(img, 250, 260, 1030, 500, (10, 14, 28))
        fill_rect(img, 258, 268, 1022, 492, (28, 20, 20))
        blit_text(img, 360, 300, "GAME OVER", C_OVER, scale=7, gap=2)
        blit_text(img, 320, 400, "SCORE:%d  PRESS ANY BTN" % game.score, C_TEXT, scale=3, gap=1)


def present(hdmi, canvas):
    frame = hdmi.newframe()
    np.copyto(frame, canvas)
    hdmi.writeframe(frame)


def main() -> int:
    log("snake: starting pid=%s" % os.getpid())
    download_raw = os.environ.get("SNAKE_DOWNLOAD", "0").strip().lower()
    download = download_raw in ("1", "true", "yes")
    log("snake: loading base overlay download=%s (eth may drop)" % download)
    try:
        base = BaseOverlay("base.bit", download=download)
    except Exception as exc:
        log("snake: overlay load failed (%s), retry with download=True" % exc)
        base = BaseOverlay("base.bit", download=True)
    log("snake: overlay loaded")

    hdmi = base.video.hdmi_out
    hdmi.cacheable_frames = False
    hdmi.configure(VideoMode(WIDTH, HEIGHT, 24), PIXEL_RGB)
    hdmi.start()
    log("snake: HDMI %dx%d started" % (WIDTH, HEIGHT))

    buttons = Buttons(base.buttons)
    game = SnakeGame()
    running = True

    def _stop(signum, _frame):
        nonlocal running
        log("snake: signal %s, stopping" % signum)
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    background = make_background()
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    draw_board(canvas, game, background)
    present(hdmi, canvas)
    log("snake: first frame presented, waiting for button")

    last_tick = time.time()
    last_heartbeat = time.time()
    dirty = False
    try:
        while running:
            now = time.time()
            edges = buttons.poll()
            if game.alive:
                for i in edges:
                    log("snake: btn%d edge dir=%s started=%s" % (i, DIRS[i], game.started))
                    game.queue_dir(DIRS[i])
            elif edges:
                log("snake: restart after game over, last score=%d" % game.score)
                game.reset()
                dirty = True
                last_tick = now

            if now - last_tick >= TICK_S:
                last_tick = now
                if game.started and game.alive:
                    game.step()
                    dirty = True

            if dirty:
                draw_board(canvas, game, background)
                present(hdmi, canvas)
                dirty = False

            if now - last_heartbeat >= 5.0:
                log(
                    "snake: alive=%s started=%s score=%d len=%d dir=%s btns=%s"
                    % (
                        game.alive,
                        game.started,
                        game.score,
                        len(game.snake),
                        game.direction,
                        buttons._stable,
                    )
                )
                last_heartbeat = now

            time.sleep(POLL_S)
    finally:
        log("snake: closing HDMI")
        try:
            hdmi.stop()
        except Exception as exc:
            log("snake: hdmi.stop error: %s" % exc)
        try:
            hdmi.close()
        except Exception as exc:
            log("snake: hdmi.close error: %s" % exc)
        log("snake: exit")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
