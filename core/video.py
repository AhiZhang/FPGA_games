import os

import numpy as np
from pynq.lib.video import PIXEL_RGB, VideoMode
from pynq.overlays.base import BaseOverlay

from .constants import HEIGHT, WIDTH


def log(msg):
    print(msg, flush=True)


def open_hdmi():
    download_raw = os.environ.get("FPGA_DOWNLOAD", os.environ.get("SNAKE_DOWNLOAD", "0"))
    download = download_raw.strip().lower() in ("1", "true", "yes")
    log("video: loading base overlay download=%s (eth may drop)" % download)
    try:
        base = BaseOverlay("base.bit", download=download)
    except Exception as exc:
        log("video: overlay load failed (%s), retry with download=True" % exc)
        base = BaseOverlay("base.bit", download=True)
    log("video: overlay loaded")
    hdmi = base.video.hdmi_out
    hdmi.cacheable_frames = False
    hdmi.configure(VideoMode(WIDTH, HEIGHT, 24), PIXEL_RGB)
    hdmi.start()
    log("video: HDMI %dx%d started" % (WIDTH, HEIGHT))
    return base, hdmi


def present(hdmi, canvas):
    frame = hdmi.newframe()
    np.copyto(frame, canvas)
    hdmi.writeframe(frame)


def close_hdmi(hdmi):
    log("video: closing HDMI")
    try:
        hdmi.stop()
    except Exception as exc:
        log("video: hdmi.stop error: %s" % exc)
    try:
        hdmi.close()
    except Exception as exc:
        log("video: hdmi.close error: %s" % exc)
