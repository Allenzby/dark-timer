# -*- coding: utf-8 -*-
"""截取 exe 完整窗口（含标题栏），并放大左上角图标区域"""
import ctypes
import sys
import time
from ctypes import wintypes
from PIL import Image, ImageGrab

user32 = ctypes.windll.user32

hwnd = user32.FindWindowW(None, "计时器")
if not hwnd:
    raise SystemExit("窗口未找到，exe 是否在运行？")

# 置顶（正确声明参数类型）
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND,
                                 ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x0001 | 0x0002)
user32.SetForegroundWindow(hwnd)
time.sleep(0.5)

r = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(r))
print("rect:", r.left, r.top, r.right, r.bottom)

img = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
img.save("_dev/exe_full.png")
print("saved _dev/exe_full.png", img.size)

# 放大标题栏图标区
crop = img.crop((0, 0, 80, 40)).resize((80 * 5, 40 * 5), Image.NEAREST)
crop.save("_dev/exe_titlebar.png")
print("saved _dev/exe_titlebar.png", crop.size)
