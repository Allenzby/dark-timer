# -*- coding: utf-8 -*-
"""端到端：真实倒计时 -> 任务栏进度递减 -> 到点闪烁 -> 确认后停闪
运行：python _dev\verify_e2e.py"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk

import timer

# 不真弹窗、不真响铃
timer.messagebox.showinfo = lambda *a, **k: print("  [弹窗] 倒计时结束，时间到！")
timer.App._alarm_sound = lambda self: None

root = tk.Tk()
app = timer.App(root)
root.update()
print("ok =", app.tb._ok, "闪烁中 =", app.tb._flashing)

for ent, v in zip(app.cd_entries, ("0", "0", "4")):
    ent.delete(0, "end")
    ent.insert(0, v)
root.iconify()
root.update()
app._primary_action()

samples = []
end = time.time() + 5.0
while time.time() < end:
    root.update()
    time.sleep(0.1)
    samples.append((app.cd_state, app.tb._last_value, app.tb._state))

print("任务栏值采样（state, value, progress_state）:")
last = None
for s in samples:
    if s != last:
        print("  ", s)
    last = s

vals = [v for _, v, _ in samples if v is not None]
drained = bool(vals) and vals[-1] < vals[0]
print("进度递减:", drained, "(%s -> %s)" % (vals[0] if vals else "-",
                                            vals[-1] if vals else "-"))
print("最终: cd_state =", app.cd_state, "进度状态 =", app.tb._state,
      "(4=红/到点, 应为 4)")

app._show_alarm_dialog()      # 模拟用户确认弹窗
print("确认弹窗后停止闪烁:", not app.tb._flashing)

print("PASS" if (drained and app.cd_state == "finished"
                 and app.tb._state == timer.TB_ERROR
                 and not app.tb._flashing) else "FAIL")
root.destroy()
