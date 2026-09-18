# HDMI Snake

Classic snake on PYNQ-Z2 HDMI OUT, controlled by BTN0–3.

- BTN0 left, BTN1 down, BTN2 up, BTN3 right
- Debounced; one direction change per tick; no 180° reverse
- Eat food to grow and score; hit wall or self to end
- Game over: BTN0 returns to the launcher menu; any other button restarts

This game is launched from the HDMI menu (`launcher.py`), not as a standalone process.
