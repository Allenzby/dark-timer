# -*- coding: utf-8 -*-
"""受控实验：手动 SetProgressValue(50%) vs TB_NONE，任务栏差异 = 进度条
运行：python _dev\verify_taskbar.py（会短暂截取任务栏底部 64px）"""
import ctypes
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageGrab, ImageChops

import timer
import tkinter as tk

OUT = Path(__file__).resolve().parent

root = tk.Tk()
app = timer.App(root)
root.update()
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
buf = ctypes.create_unicode_buffer(64)
ctypes.windll.user32.GetClassNameW(app.tb._hwnd, buf, 64)
print("ok =", app.tb._ok, "hwnd =", app.tb._hwnd, "类名 =", buf.value)


def shot(name):
    img = ImageGrab.grab(bbox=(0, sh - 64, sw, sh))
    img.save(OUT / name)
    return img


# 让窗口进入后台并静止
root.iconify()
root.update()
time.sleep(0.6)

# A: 50% 进度（正常色）
app.tb._state = None          # 强制重发
app.tb._last_value = None
app.tb.progress(5000, 10000, timer.TB_NORMAL)
time.sleep(0.6)
a = shot("tb_on.png")

# B: 关闭进度
app.tb.set_state(timer.TB_NONE)
time.sleep(0.6)
b = shot("tb_off.png")

# C: 再开一次，确认可重复
app.tb._state = None
app.tb.progress(5000, 10000, timer.TB_NORMAL)
time.sleep(0.6)
c = shot("tb_on2.png")

d1 = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
d2 = ImageChops.difference(a.convert("RGB"), c.convert("RGB"))
n1 = sum(1 for p in d1.getdata() if sum(p) > 30)
n2 = sum(1 for p in d2.getdata() if sum(p) > 30)
print("ON vs OFF  差异bbox:", d1.getbbox(), "像素:", n1)
print("ON vs ON2  差异bbox:", d2.getbbox(), "像素:", n2, "(应为 0=可重复)")

if d1.getbbox() and n1 > 100:
    from collections import Counter
    x0, y0, x1, y1 = d1.getbbox()
    dp, pa, pb = d1.load(), a.load(), b.load()
    ca, cb = Counter(), Counter()
    for y in range(y0, y1):
        for x in range(x0, x1):
            if sum(dp[x, y]) > 30:
                ca[pa[x, y]] += 1
                cb[pb[x, y]] += 1
    print("开时颜色 top3:", ca.most_common(3))
    print("关时颜色 top3:", cb.most_common(3))
    print("区域 %dx%d（50%% 进度 -> 填充约占按钮一半）" % (x1 - x0, y1 - y0))
    pad = 20
    box = (max(0, x0 - pad), max(0, y0 - pad),
           min(x1 + pad, sw), min(y1 + pad, 64))
    a.crop(box).resize(((box[2] - box[0]) * 6, (box[3] - box[1]) * 6),
                       Image.NEAREST).save(OUT / "tb_bar_zoom.png")
    print("saved tb_bar_zoom.png")
    print("PASS" if n1 > 100 and n2 == 0 else "FAIL")

root.destroy()
