#!/usr/bin/env python3
"""HDMI launcher: pick a game with BTN0-3, then run it."""
from __future__ import annotations

import os
import signal
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.buttons import Buttons
from core.constants import POLL_S
from core.gfx import blank_frame
from core.menu import GameMenu
from core.video import close_hdmi, open_hdmi, present
from games import GAMES


def log(msg):
    print(msg, flush=True)


def main() -> int:
    log("launcher: starting pid=%s" % os.getpid())
    base, hdmi = open_hdmi()
    buttons = Buttons(base.buttons)
    menu = GameMenu(GAMES)
    scene = None
    running = True

    def _stop(signum, _frame):
        nonlocal running
        log("launcher: signal %s, stopping" % signum)
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    canvas = blank_frame()
    menu.draw(canvas)
    present(hdmi, canvas)
    log("launcher: menu on HDMI, waiting for select")

    last_tick = time.time()
    last_heartbeat = time.time()
    dirty = False
    try:
        while running:
            now = time.time()
            edges = buttons.poll()
            if scene is None:
                if edges:
                    log("launcher: menu buttons %s index=%d" % (edges, menu.index))
                    menu.handle_buttons(edges)
                    if menu.choice is not None:
                        factory = menu.choice["factory"]
                        log("launcher: start %s" % menu.choice["id"])
                        scene = factory()
                        last_tick = now
                    dirty = True
            else:
                if edges:
                    log("launcher: game buttons %s" % (edges,))
                    scene.handle_buttons(edges)
                    dirty = True
                if scene.wants_menu():
                    log("launcher: back to menu")
                    scene = None
                    dirty = True
                    last_tick = now
                elif now - last_tick >= getattr(scene, "tick_s", 0.16):
                    last_tick = now
                    if scene.needs_tick():
                        scene.tick()
                        dirty = True

            if dirty:
                if scene is None:
                    menu.draw(canvas)
                else:
                    scene.draw(canvas)
                present(hdmi, canvas)
                dirty = False

            if now - last_heartbeat >= 5.0:
                mode = "menu" if scene is None else type(scene).__name__
                log(
                    "launcher: mode=%s index=%d btns=%s"
                    % (mode, menu.index, buttons._stable)
                )
                last_heartbeat = now

            time.sleep(POLL_S)
    finally:
        close_hdmi(hdmi)
        log("launcher: exit")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
