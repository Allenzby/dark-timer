# -*- coding: utf-8 -*-
"""验证打包后的 exe 标题栏是否深色（自动启动 exe -> 量色 -> 截图 -> 关闭）

运行：python _dev\check_titlebar_exe.py
"""
import ctypes
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
EXE = ROOT_DIR / "dist" / "计时器.exe"
OUT = ROOT_DIR / "_dev" / "titlebar_shot.png"

sys.path.insert(0, str(ROOT_DIR))
import timer   # noqa: E402
import winshot  # noqa: E402

user32 = ctypes.windll.user32
user32.GetWindowRect.argtypes = [ctypes.c_void_p,
                                 ctypes.POINTER(ctypes.c_long * 4)]
user32.GetClientRect.argtypes = [ctypes.c_void_p,
                                 ctypes.POINTER(ctypes.c_long * 4)]
user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
user32.IsWindowVisible.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p,
                                  ctypes.c_int]


def find_window(title):
    """按标题找可见顶层窗口"""
    found = []
    ENUM = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)

    @ENUM
    def cb(hwnd, _l):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if buf.value == title:
                found.append(hwnd)
        return 1

    user32.EnumWindows(cb, 0)
    return found[0] if found else 0


def rect(hwnd):
    r = (ctypes.c_long * 4)()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r[0], r[1], r[2], r[3]


def caption_color(hwnd):
    """取标题栏底色：PrintWindow 抓窗口自身像素（不受遮挡），取出现最多的颜色"""
    x1, y1, x2, y2 = rect(hwnd)
    c = (ctypes.c_long * 4)()
    user32.GetClientRect(hwnd, ctypes.byref(c))
    cap = (y2 - y1) - c[3]
    if cap < 16:
        cap = 32
    w = x2 - x1
    img = winshot.grab_hwnd(hwnd, (x1, y1, x2, y2))
    img.save(OUT)
    colors = img.crop((0, 0, w, cap)).convert("RGB").getcolors(1000000)
    return max(colors)[1] if colors else None


if not EXE.exists():
    raise SystemExit("找不到 exe，请先打包：dist\\计时器.exe")

proc = subprocess.Popen([str(EXE)])
try:
    hwnd = 0
    for _ in range(40):               # 最多等 8 秒
        time.sleep(0.2)
        hwnd = find_window("计时器")
        if hwnd:
            break
    if not hwnd:
        raise SystemExit("exe 窗口未出现")

    x1, y1, x2, y2 = rect(hwnd)
    print("exe 窗口：{}x{}  位置 ({},{})".format(x2 - x1, y2 - y1, x1, y1))
    color = caption_color(hwnd)
    lum = (color[0] * 299 + color[1] * 587 + color[2] * 114) // 1000
    print("标题栏颜色：RGB{}  亮度 {}".format(color, lum))
    print("截图：_dev\\titlebar_shot.png")
    ok = lum < 90
    print("[{}] exe 标题栏为深色".format("PASS" if ok else "FAIL"))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()

sys.exit(0 if ok else 1)
