# -*- coding: utf-8 -*-
"""界面截图：把实际运行的窗口截成 PNG 用于检查
运行：python _dev\shot.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk
import winshot
import timer

# 截图输出到项目根目录的 screenshots\（README 展示用）
OUT_DIR = Path(__file__).resolve().parent.parent / "screenshots"
OUT_DIR.mkdir(exist_ok=True)


def pump(root, seconds):
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.02)


root = tk.Tk()
app = timer.App(root)
root.attributes("-topmost", True)
root.lift()
root.focus_force()
pump(root, 0.5)


def snap(name):
    img = winshot.grab("计时器")
    img.save(OUT_DIR / name)
    print("screenshots\\" + name, img.size)


# 1) 倒计时待机
snap("shot1_countdown.png")

# 2) 倒计时运行中（25分钟预设，跑 2 秒）
app._set_preset(25)
app._primary_action()
pump(root, 2.0)
snap("shot2_running.png")
app._reset()

# 3) 秒表 + 两条计次
app._switch_mode("stopwatch")
root.update()
app._sw_toggle()
pump(root, 1.35)
app._lap()
pump(root, 0.82)
app._lap()
pump(root, 0.3)
snap("shot3_stopwatch.png")
app._sw_toggle()

root.destroy()
print("done")
