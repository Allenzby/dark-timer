# -*- coding: utf-8 -*-
"""把界面按 150% 缩放渲染并存成图，用于肉眼确认高分屏下不挤、不裁切。

运行：python _dev\shot_dpi150.py
"""
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk  # noqa: E402

import winshot  # noqa: E402
import timer  # noqa: E402

SCALING = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0  # 2.0 ≈ 150%

root = tk.Tk()
root.tk.call("tk", "scaling", SCALING)
app = timer.App(root)
root.attributes("-topmost", True)
root.lift()
root.focus_force()

end = time.time() + 0.6
while time.time() < end:
    root.update()
    time.sleep(0.02)

img = winshot.grab("计时器")
name = "_dev/dpi{:d}.png".format(int(round(SCALING * 72 / 96 * 100)))
img.save(ROOT_DIR / name)
print("SCALE = {:.2f} -> {}  ({}x{})".format(timer.SCALE, name, *img.size))
root.destroy()
