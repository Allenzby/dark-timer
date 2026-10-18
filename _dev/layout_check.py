# -*- coding: utf-8 -*-
"""布局自检：打印控件相对窗口的绝对坐标，验证水平居中
运行：python _dev\layout_check.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk
import timer

root = tk.Tk()
app = timer.App(root)
root.update()

RW, RH = root.winfo_rootx(), root.winfo_rooty()
W = root.winfo_width()


def absx(w):
    return w.winfo_rootx() - RW


def show(name, w):
    print("{:<16} left={:<4} right={:<4} center={}".format(
        name, absx(w), absx(w) + w.winfo_width(),
        absx(w) + w.winfo_width() // 2))


def row_center(name, first, last):
    left = absx(first)
    right = absx(last) + last.winfo_width()
    c = (left + right) // 2
    print("{:<16} group=[{}..{}] center={} (window center={}) -> {}".format(
        name, left, right, c, W // 2,
        "CENTERED" if abs(c - W // 2) <= 10 else "OFF!"))


print("=== 倒计时模式 ===")
show("lbl_time", app.lbl_time)
show("lbl_status", app.lbl_status)
row_center("entries行", app.cd_entries[0], app.cd_entries[-1])
row_center("presets行", app.preset_buttons[0], app.preset_buttons[-1])
row_center("actions", app.btn_primary, app.btn_reset)

bottom = 0


def mark(w):
    global bottom
    bottom = max(bottom, w.winfo_rooty() - root.winfo_rooty() + w.winfo_height())


mark(app.btn_primary)
mark(app.btn_reset)
for c in root.children.values():
    if isinstance(c, tk.Label) and "空格" in str(c.cget("text")):
        mark(c)
print("content bottom:", bottom, "/ window h:", root.winfo_height(), "->",
      "OK" if bottom <= root.winfo_height() else "OVERFLOW!")

print()
print("=== 秒表模式 ===")
app._switch_mode("stopwatch")
root.update()
row_center("actions(3钮)", app.btn_lap, app.btn_reset)
show("btn_lap", app.btn_lap)
show("btn_primary", app.btn_primary)
show("btn_reset", app.btn_reset)
print("lap_list:", app.lap_list.winfo_height(), "px高")
bottom = c.winfo_rooty() + c.winfo_height() - root.winfo_rooty()
print("content bottom:", bottom, "->", "OK" if bottom <= root.winfo_height() else "OVERFLOW!")

root.destroy()
