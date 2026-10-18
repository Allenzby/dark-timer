# -*- coding: utf-8 -*-
"""功能测试：不依赖肉眼，自动验证倒计时/秒表/置顶逻辑
运行：python _dev\test_timer.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk
import timer

# 静音 & 不弹窗（弹窗会阻塞测试）
timer._ALARM_CALLED = False
timer.messagebox.showinfo = lambda *a, **k: setattr(timer, "_ALARM_CALLED", True)
timer.App._alarm_sound = staticmethod(lambda: None)

results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print("[{}] {} {}".format("PASS" if cond else "FAIL", name, extra))


def pump(root, seconds):
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        time.sleep(0.02)


root = tk.Tk()
app = timer.App(root)
root.update()

# ---------- 1. 初始状态 ----------
check("初始显示 00:00:00", app.lbl_time.cget("text") == "00:00:00")
check("初始输入框全为0",
      [e.get() for e in app.cd_entries] == ["0", "0", "0"],
      str([e.get() for e in app.cd_entries]))
check("初始状态 idle", app.cd_state == "idle")

# ---------- 2. 倒计时 2 秒走完 ----------
for ent, v in zip(app.cd_entries, ("0", "0", "2")):
    ent.delete(0, "end")
    ent.insert(0, v)
app._primary_action()
check("开始后 running", app.cd_state == "running")
check("输入框已锁定", str(app.cd_entries[0].cget("state")) == "disabled")
check("按钮变暂停", app.btn_primary.cget("text") == "暂停")
pump(root, 0.6)
t = app.lbl_time.cget("text")
check("0.6秒后显示 00:00:02/01", t in ("00:00:02", "00:00:01"), t)
pump(root, 1.8)
check("走完变 finished", app.cd_state == "finished")
check("显示归零", app.lbl_time.cget("text") == "00:00:00")
check("弹窗已触发", timer._ALARM_CALLED)
check("提示音线程已触发", timer.App._alarm_sound is not None)
check("结束时输入框解锁", str(app.cd_entries[0].cget("state")) == "normal")

# ---------- 3. 暂停 / 继续 用时准确性 ----------
for ent, v in zip(app.cd_entries, ("0", "0", "10")):
    ent.delete(0, "end")
    ent.insert(0, v)
app._primary_action()          # 重新开始 10 秒
pump(root, 1.0)
app._primary_action()          # 暂停
check("暂停状态", app.cd_state == "paused")
r1 = app.cd_remaining
check("暂停约剩 9 秒", 8.5 < r1 < 9.2, "remain=%.2f" % r1)
pump(root, 0.5)
r2 = app.cd_remaining
check("暂停期间时间不走", abs(r2 - r1) < 0.01, "%.2f->%.2f" % (r1, r2))
check("暂停按钮变继续", app.btn_primary.cget("text") == "继续")
app._primary_action()          # 继续
check("恢复 running", app.cd_state == "running")
pump(root, 0.4)
check("恢复后继续走", app.cd_remaining < r2 - 0.2)
app._reset()
check("重置回 idle", app.cd_state == "idle")
check("重置后显示 00:00:00", app.lbl_time.cget("text") == "00:00:00",
      app.lbl_time.cget("text"))
check("重置后输入框全为0",
      [e.get() for e in app.cd_entries] == ["0", "0", "0"],
      str([e.get() for e in app.cd_entries]))

# ---------- 4. 快捷时长 & 非法输入 ----------
app._set_preset(25)
check("预设25分钟", app.lbl_time.cget("text") == "00:25:00",
      app.lbl_time.cget("text"))
for ent in app.cd_entries:
    ent.delete(0, "end")
app._entries_changed()
check("清空后显示 00:00:00", app.lbl_time.cget("text") == "00:00:00")
warned = []
timer.messagebox.showwarning = lambda *a, **k: warned.append(a)
app._primary_action()
check("空时间不启动并警告", app.cd_state == "idle" and len(warned) == 1)

# ---------- 5. 秒表 ----------
app._switch_mode("stopwatch")
root.update()
check("切换到秒表", app.mode == "stopwatch")
check("计次按钮可见", app.btn_lap.winfo_ismapped())
check("倒计时控件隐藏", not app.cd_box.winfo_ismapped())
app._sw_toggle()
check("秒表运行", app.sw_running)
pump(root, 0.5)
app._lap()
check("计次 1 条", len(app.laps) == 1)
pump(root, 0.3)
app._lap()
check("计次 2 条", len(app.laps) == 2)
check("列表 2 行", app.lap_list.size() == 2)
check("最新在顶部", str(app.lap_list.get(0)).startswith("#2"))
elapsed_before = app._sw_elapsed()
app._sw_toggle()               # 暂停
check("秒表暂停", not app.sw_running)
pump(root, 0.4)
check("暂停后时间冻结", abs(app._sw_elapsed() - elapsed_before) < 0.01)
check("按钮变开始", app.btn_primary.cget("text") == "开始")
app._reset()
check("秒表重置归零", app._sw_elapsed() == 0.0 and len(app.laps) == 0)
check("列表清空", app.lap_list.size() == 0)

# ---------- 6. 置顶开关 ----------
check("初始不置顶", not app.pinned and not root.attributes("-topmost"))
app._toggle_pin()
root.update()
check("点击后置顶", app.pinned and bool(root.attributes("-topmost")))
app._toggle_pin()
root.update()
check("再点取消置顶", not app.pinned and not root.attributes("-topmost"))

# ---------- 7. 切回倒计时 ----------
app._switch_mode("countdown")
check("切回倒计时", app.mode == "countdown")
check("计次按钮已隐藏", not app.btn_lap.winfo_ismapped())

root.destroy()

# ---------- 汇总 ----------
fails = [n for n, ok in results if not ok]
print("\n共 {} 项，失败 {} 项".format(len(results), len(fails)))
if fails:
    for n in fails:
        print("  FAIL:", n)
    raise SystemExit(1)
print("ALL PASS")
