# -*- coding: utf-8 -*-
"""验证标题栏是否变深色：量主窗口和弹窗标题栏的实际像素颜色

运行：python _dev\verify_titlebar.py
"""
import ctypes
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))   # 为了 import winshot

import tkinter as tk            # noqa: E402
from tkinter import messagebox  # noqa: E402

import timer   # noqa: E402
import winshot  # noqa: E402

user32 = ctypes.windll.user32
user32.GetWindowRect.argtypes = [ctypes.c_void_p,
                                 ctypes.POINTER(ctypes.c_long * 4)]
user32.GetClientRect.argtypes = [ctypes.c_void_p,
                                 ctypes.POINTER(ctypes.c_long * 4)]
user32.GetForegroundWindow.restype = ctypes.c_void_p
user32.GetWindowThreadProcessId.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
user32.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                ctypes.c_size_t, ctypes.c_size_t]
user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
user32.IsWindowVisible.restype = ctypes.c_int


def rect(hwnd):
    r = (ctypes.c_long * 4)()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r[0], r[1], r[2], r[3]


def client_h(hwnd):
    c = (ctypes.c_long * 4)()
    user32.GetClientRect(hwnd, ctypes.byref(c))
    return c[3] - c[1]


def caption_color(hwnd, method="pw", name=""):
    """取标题栏底色，返回出现最多的颜色（白字/按钮只占少数像素，不会干扰）。

    method="pw"      PrintWindow 抓窗口自身像素，遮挡也不影响（主窗口可用）
    method="screen   抓屏幕像素；对话框的 DWM 标题栏 PrintWindow 画不出来（返回白）
    """
    x1, y1, x2, y2 = rect(hwnd)
    w, h = x2 - x1, y2 - y1
    cap = (y2 - y1) - client_h(hwnd)
    if cap < 16:
        cap = 32

    if method == "pw":
        strip = winshot.grab_hwnd(hwnd, (x1, y1, x2, y2)).crop((0, 0, w, cap))
        tag = "printwindow"
    else:
        from PIL import ImageGrab
        strip = ImageGrab.grab(bbox=(x1, y1, x2, y1 + cap))
        tag = "screen"
    strip = strip.convert("RGB")
    strip.save(str(Path(__file__).resolve().parent /
                   "titlebar_{}.png".format(name or method)))

    colors = strip.getcolors(maxcolors=1000000)
    if not colors:
        print("  取样失败：w={} cap={} hwnd={} via={}".format(w, cap, hwnd, tag))
        return None
    color = max(colors)[1]
    print("  取样方式={}  标题栏高={}  底色={}".format(tag, cap, color))
    return color


def describe(c):
    if c is None:
        return "取样失败"
    lum = (c[0] * 299 + c[1] * 587 + c[2] * 114) // 1000
    return "RGB{}  亮度{}  {}".format(c, lum, "深色 ✓" if lum < 90 else "浅色 ✗")


fails = []


def check(name, ok, detail=""):
    print("[{}] {}  {}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        fails.append(name)


# ---------------- 主窗口 ----------------
root = tk.Tk()
app = timer.App(root)
root.attributes("-topmost", True)
root.lift()
root.focus_force()
end = time.time() + 0.6
while time.time() < end:
    root.update()
    time.sleep(0.02)

main_hwnd = timer.top_hwnd(root)
print("主窗口 hwnd =", main_hwnd)
check("DWM 深色属性设置成功",
      bool(timer.enable_dark_titlebar(main_hwnd)))

time.sleep(0.3)
c = caption_color(main_hwnd, "pw", "main")
print("主窗口标题栏 ->", describe(c))
check("主窗口标题栏为深色", c is not None and (c[0] * 299 + c[1] * 587 +
                                             c[2] * 114) // 1000 < 90,
      describe(c))

# ---------------- 弹窗标题栏 ----------------
result = {}


def our_dialogs():
    """枚举本进程除主窗口外的可见顶层窗口（弹窗）"""
    found = []
    ENUM = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
    me = os.getpid()

    @ENUM
    def cb(hwnd, _lparam):
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if (pid.value == me and hwnd != main_hwnd
                and user32.IsWindowVisible(hwnd)):
            found.append(hwnd)
        return 1

    user32.EnumWindows(cb, 0)
    return found


def watcher():
    """等弹窗出现，取色后关掉它"""
    until = time.time() + 12
    while time.time() < until:
        dialogs = our_dialogs()
        if dialogs:
            hwnd = dialogs[0]
            print("  找到弹窗 hwnd =", hwnd, "rect =", rect(hwnd),
                  "client_h =", client_h(hwnd))
            time.sleep(0.3)                # 等标题栏绘制完
            result["color"] = caption_color(hwnd, "screen", "dialog")
            user32.PostMessageW(hwnd, 0x0010, 0, 0)   # WM_CLOSE
            return
        time.sleep(0.1)
    print("  超时：没找到本进程的弹窗")


threading.Thread(target=watcher, daemon=True).start()
root.after(900, lambda: app._dialog(messagebox.showwarning, "计时器", "测试弹窗"))
root.after(900 + 4000, root.quit)
root.mainloop()

c2 = result.get("color")
print("弹窗标题栏   ->", describe(c2))
check("弹窗标题栏为深色", c2 is not None and (c2[0] * 299 + c2[1] * 587 +
                                             c2[2] * 114) // 1000 < 90,
      describe(c2))

root.destroy()
print("\n" + ("全部通过" if not fails else "失败：{}".format(fails)))
sys.exit(1 if fails else 0)
