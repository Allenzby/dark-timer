# -*- coding: utf-8 -*-
"""按窗口句柄直接抓取「计时器」窗口内容（PrintWindow，不受遮挡影响）"""
import ctypes
import time
from ctypes import wintypes
from PIL import Image, ImageGrab

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def grab_printwindow(hwnd, w, h):
    hdc = user32.GetDC(0)
    memdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(memdc, bmp)
    ok = user32.PrintWindow(hwnd, memdc, 3)  # PW_RENDERFULLCONTENT
    bi = BITMAPINFOHEADER()
    bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.biWidth, bi.biHeight = w, -h           # 自上而下
    bi.biPlanes, bi.biBitCount = 1, 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(memdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    gdi32.SelectObject(memdc, 0)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(memdc)
    user32.ReleaseDC(0, hdc)
    if not ok:
        return None
    img = Image.frombuffer("RGBA", (w, h), buf.raw, "raw", "BGRA", 0, 1)
    return img


def grab_front(hwnd, w, h):
    """兜底：置顶后屏幕抓取"""
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND,
                                     ctypes.c_int, ctypes.c_int,
                                     ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x0001 | 0x0002)
    time.sleep(0.4)
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))


hwnd = user32.FindWindowW(None, "计时器")
if not hwnd:
    raise SystemExit("窗口未找到")

rect = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rect))
w, h = rect.right - rect.left, rect.bottom - rect.top
print("hwnd:", hwnd, "size:", w, "x", h)

img = grab_printwindow(hwnd, w, h)
used = "PrintWindow"
if img is None:
    img = grab_front(hwnd, w, h)
    used = "front-grab"

# 检查是否空白（绝大多数像素同色）
colors = img.convert("RGB").getcolors(maxcolors=1000000)
top = max(colors)[0]
print("方式:", used, "最大同色像素占比: {:.0%}".format(top / (w * h)))
if top / (w * h) > 0.95 and used == "PrintWindow":
    print("PrintWindow 输出疑似空白，改用置顶抓取")
    img = grab_front(hwnd, w, h)
    used = "front-grab(兜底)"

img.save("exe_shot.png")
print("saved exe_shot.png", img.size, "方式:", used)
