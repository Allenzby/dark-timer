# -*- coding: utf-8 -*-
"""验证高分屏适配：模拟 150% / 200% 缩放，检查布局是否被裁切。

用法：python _dev/verify_dpi.py
纯 Tk，无第三方依赖；不修改系统设置。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk  # noqa: E402

import timer  # noqa: E402

fails = []


def check(name, ok, detail=""):
    print("[{}] {}{}".format("PASS" if ok else "FAIL", name,
                             "  " + detail if detail else ""))
    if not ok:
        fails.append(name)


def probe(scaling, label):
    """用指定的 tk scaling（每磅像素数）起一套界面，量一遍尺寸"""
    root = tk.Tk()
    root.tk.call("tk", "scaling", scaling)
    app = timer.App(root)
    root.update_idletasks()

    w, h = root.winfo_width(), root.winfo_height()
    digit_w = app.lbl_time.winfo_reqwidth()
    digit_h = app.lbl_time.winfo_reqheight()
    need_w = root.winfo_reqwidth()
    need_h = root.winfo_reqheight()

    print("\n=== {}  scaling={}  DPI≈{:.0f}  SCALE={:.2f} ===".format(
        label, scaling, scaling * 72, timer.SCALE))
    print("  窗口 {}x{}   内容需要 {}x{}".format(w, h, need_w, need_h))
    print("  数字区 {}x{}".format(digit_w, digit_h))

    check("{}: 布局系数 ≈ {:.2f}".format(label, scaling * 72 / 96),
          abs(timer.SCALE - scaling * 72 / 96) < 0.02,
          "实际 {:.3f}".format(timer.SCALE))
    check("{}: 窗口按系数放大".format(label),
          abs(w - int(round(470 * timer.SCALE))) <= 2,
          "{} ≈ {}".format(w, int(round(470 * timer.SCALE))))
    check("{}: 内容宽度不超窗口".format(label),
          need_w <= w,
          "需要 {} / 可用 {}".format(need_w, w))
    check("{}: 大数字不裁切".format(label),
          digit_w <= w - timer.px(20),
          "数字 {} / 可用 {}".format(digit_w, w - timer.px(20)))
    check("{}: 内容高度不超窗口".format(label),
          need_h <= h,
          "需要 {} / 可用 {}".format(need_h, h))

    root.destroy()


probe(96 / 72.0, "100%")
probe(144 / 72.0, "150%")
probe(192 / 72.0, "200%")

print("\n" + ("全部通过 ({} 项)".format(5 * 3) if not fails else
              "失败 {} 项: {}".format(len(fails), fails)))
sys.exit(1 if fails else 0)
