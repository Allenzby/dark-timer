# -*- coding: utf-8 -*-
"""探测：Tk 窗口 HWND 归属 + ITaskbarList3 COM 接口是否可调"""
import ctypes
import time
import tkinter as tk
from ctypes import wintypes

ole32 = ctypes.windll.ole32
user32 = ctypes.windll.user32

# ---- GUID ----
class GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)]


def guid(s):
    s = s.strip("{}")
    p = s.split("-")
    g = GUID()
    g.Data1 = int(p[0], 16)
    g.Data2 = int(p[1], 16)
    g.Data3 = int(p[2], 16)
    b = bytes.fromhex(p[3] + p[4])
    for i, v in enumerate(b):
        g.Data4[i] = v
    return g


def vcall(obj, idx, restype, argtypes, *args):
    """按 COM vtable 下标调用"""
    vtbl = ctypes.cast(obj, ctypes.POINTER(ctypes.c_void_p))[0]
    fn = ctypes.cast(vtbl, ctypes.POINTER(ctypes.c_void_p))[idx]
    proto = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
    return proto(fn)(obj, *args)


# ---- Tk 窗口句柄探测 ----
root = tk.Tk()
root.title("计时器")
root.update()

wid = root.winfo_id()
cls_buf = ctypes.create_unicode_buffer(64)
user32.GetClassNameW(wid, cls_buf, 64)
print("winfo_id() =", wid, "类名 =", cls_buf.value)

parent = user32.GetParent(wid)
user32.GetClassNameW(parent, cls_buf, 64) if parent else None
print("GetParent =", parent, "类名 =", cls_buf.value if parent else "-")

# 用 FindWindow 对照
fw = user32.FindWindowW(None, "计时器")
user32.GetClassNameW(fw, cls_buf, 64)
print("FindWindow =", fw, "类名 =", cls_buf.value)
print("winfo_id == FindWindow ?", wid == fw)

# ---- COM 初始化 ----
hr = ole32.CoInitializeEx(None, 2)  # COINIT_APARTMENTTHREADED
print("CoInitializeEx hr = 0x%08X (0 或 S_OK 即可)" % (hr & 0xFFFFFFFF))

# ---- 创建 ITaskbarList3 ----
clsid = guid("{56FDF344-FD6D-11d0-958A-006097C9A090}")   # TaskbarList
iid = guid("{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}")     # ITaskbarList3
p = ctypes.c_void_p()
ole32.CoCreateInstance.argtypes = [ctypes.POINTER(GUID), ctypes.c_void_p,
                                   ctypes.c_ulong, ctypes.POINTER(GUID),
                                   ctypes.POINTER(ctypes.c_void_p)]
hr = ole32.CoCreateInstance(ctypes.byref(clsid), None, 0x1,   # CLSCTX_INPROC_SERVER
                            ctypes.byref(iid), ctypes.byref(p))
print("CoCreateInstance hr = 0x%08X  ptr = 0x%X" % (hr & 0xFFFFFFFF, p.value or 0))
if hr != 0:
    raise SystemExit("COM 创建失败")

HRESULT = ctypes.c_long
print("HrInit hr = 0x%08X" % (vcall(p, 3, HRESULT, ()) & 0xFFFFFFFF))

hwnd = wid
# 测试：设置进度 60/100
hr1 = vcall(p, 9, HRESULT, (wintypes.HWND, ctypes.c_ulong, ctypes.c_ulong),
            hwnd, 60, 100)
hr2 = vcall(p, 10, HRESULT, (wintypes.HWND, ctypes.c_ulong), hwnd, 2)  # NORMAL
print("SetProgressValue hr = 0x%08X" % (hr1 & 0xFFFFFFFF))
print("SetProgressState  hr = 0x%08X" % (hr2 & 0xFFFFFFFF))

time.sleep(2)

# 清除
hr3 = vcall(p, 10, HRESULT, (wintypes.HWND, ctypes.c_ulong), hwnd, 0)
print("清除 hr = 0x%08X" % (hr3 & 0xFFFFFFFF))

# ---- FlashWindowEx ----
class FLASHWINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("hwnd", wintypes.HWND),
                ("dwFlags", ctypes.c_ulong), ("uCount", ctypes.c_ulong),
                ("dwTimeout", ctypes.c_ulong)]


fwinfo = FLASHWINFO()
fwinfo.cbSize = ctypes.sizeof(FLASHWINFO)
fwinfo.hwnd = hwnd
fwinfo.dwFlags = 3 | 12   # FLASHW_ALL | FLASHW_TIMERNOFG
fwinfo.uCount = 5
fwinfo.dwTimeout = 0
r = user32.FlashWindowEx(ctypes.byref(fwinfo))
print("FlashWindowEx 返回 =", r, "(返回值是闪烁前窗口是否前台，不代表成功)")

root.destroy()
ole32.CoUninitialize()
print("探测完成")
