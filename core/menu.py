from core.constants import HEIGHT, WIDTH
from core.gfx import (
    C_ACCENT,
    C_BG,
    C_CARD,
    C_CARD_DIM,
    C_MUTED,
    C_OVER,
    C_PANEL,
    C_TEXT,
    C_TITLE,
    blit_text,
    fill_rect,
)


class GameMenu:
    """HDMI game picker. BTN2 up, BTN1 down, BTN3 play, BTN0 play if enabled."""

    def __init__(self, games):
        self.games = list(games)
        self.index = 0
        self.choice = None
        self.denied = False

    def handle_buttons(self, edges):
        self.choice = None
        self.denied = False
        n = len(self.games)
        if n == 0:
            return
        for i in edges:
            if i == 2:
                self.index = (self.index - 1) % n
            elif i == 1:
                self.index = (self.index + 1) % n
            elif i in (0, 3):
                item = self.games[self.index]
                if item.get("enabled") and item.get("factory"):
                    self.choice = item
                else:
                    self.denied = True

    def draw(self, canvas):
        canvas[:] = C_BG
        fill_rect(canvas, 0, 0, WIDTH, 110, C_PANEL)
        blit_text(canvas, 40, 28, "FPGA GAMES", C_TITLE, scale=7, gap=2)
        blit_text(canvas, 40, 82, "SELECT A GAME", C_MUTED, scale=2, gap=1)

        top = 150
        card_h = 150
        gap = 24
        for i, item in enumerate(self.games):
            y0 = top + i * (card_h + gap)
            y1 = y0 + card_h
            selected = i == self.index
            enabled = bool(item.get("enabled") and item.get("factory"))
            if selected:
                fill_rect(canvas, 48, y0 - 6, 1232, y1 + 6, C_TITLE if enabled else C_OVER)
                fill_rect(canvas, 56, y0, 1224, y1, C_CARD)
            else:
                fill_rect(canvas, 56, y0, 1224, y1, C_CARD_DIM)
            title_c = C_TITLE if enabled else C_MUTED
            sub_c = C_TEXT if enabled else (90, 100, 120)
            status = "READY" if enabled else "LOCKED"
            blit_text(canvas, 90, y0 + 36, item["title"], title_c, scale=6, gap=2)
            blit_text(canvas, 90, y0 + 96, item["subtitle"], sub_c, scale=3, gap=1)
            blit_text(canvas, 980, y0 + 60, status, C_ACCENT if enabled else C_MUTED, scale=3, gap=1)

        help_y = HEIGHT - 70
        fill_rect(canvas, 0, help_y - 16, WIDTH, HEIGHT, C_PANEL)
        blit_text(
            canvas,
            40,
            help_y,
            "BTN2 UP   BTN1 DOWN   BTN3 PLAY   BTN0 PLAY",
            C_MUTED,
            scale=3,
            gap=1,
        )
        if self.denied:
            blit_text(canvas, 40, help_y + 28, "NOT READY YET", C_OVER, scale=2, gap=1)
