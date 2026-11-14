# -*- coding: utf-8 -*-
"""在 100% 缩放下截一张图，和已有的 README 截图逐像素比较，
确认 DPI 适配没有改变默认外观。

运行：python _dev\check_dpi_visual.py
"""
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk  # noqa: E402

import winshot  # noqa: E402
import timer  # noqa: E402
from PIL import Image, ImageChops  # noqa: E402

timer.enable_dpi_awareness()
root = tk.Tk()
app = timer.App(root)
root.attributes("-topmost", True)
root.lift()
root.focus_force()

end = time.time() + 0.6
while time.time() < end:
    root.update()
    time.sleep(0.02)

img = winshot.grab("计时器")
out = ROOT_DIR / "_dev" / "dpi_shot.png"
img.save(out)
print("SCALE = {:.3f}   窗口 {}x{}".format(timer.SCALE, *img.size))
print("截图 -> _dev\\dpi_shot.png")

ref_path = ROOT_DIR / "screenshots" / "shot1_countdown.png"
if ref_path.exists():
    ref = Image.open(ref_path).convert("RGB")
    if ref.size != img.size:
        print("尺寸不同：旧 {} / 新 {}".format(ref.size, img.size))
    else:
        diff = ImageChops.difference(ref, img.convert("RGB"))
        bbox = diff.getbbox()
        hist = diff.convert("L").histogram()
        changed = sum(hist[8:])          # 明显差异的像素数
        total = img.size[0] * img.size[1]
        print("与旧截图差异像素 {}/{} ({:.3f}%)  bbox={}".format(
            changed, total, changed * 100.0 / total, bbox))
        print("结论：" + ("外观未变" if changed * 100.0 / total < 1.0 else "外观有变化"))

root.destroy()
