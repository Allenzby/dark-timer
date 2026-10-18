# -*- coding: utf-8 -*-
"""
计时器 —— 深色极简风桌面计时器
功能：
  · 倒计时（到点播放提示音 + 弹窗提醒）
  · 秒表（支持计次记录）
  · 窗口置顶开关（点击开启，再点取消）
运行：python timer.py
打包：pyinstaller --noconfirm --onefile --windowed --name 计时器 timer.py
"""

import math
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

try:
    import winsound
except ImportError:  # 非 Windows 系统
    winsound = None

# ---------------- 配色（深色极简） ----------------
BG = "#0E1013"          # 窗口底色
CARD = "#171A20"        # 卡片 / 次级按钮
CARD_HOVER = "#232833"  # 次级按钮悬停
TEXT = "#F2F4F7"        # 主文字
MUTED = "#7C828E"       # 弱化文字
ACCENT = "#3B82F6"      # 主题蓝（主按钮 / 运行状态）
ACCENT_HOVER = "#2563EB"
WARN = "#F59E0B"        # 时间到
ENTRY_BG = "#1E222B"    # 输入框底色

FONT_UI = ("Microsoft YaHei UI", 10)
FONT_UI_BOLD = ("Microsoft YaHei UI", 10, "bold")
FONT_SMALL = ("Microsoft YaHei UI", 9)
FONT_DIGIT = ("Consolas", 62, "bold")
FONT_SET = ("Consolas", 16, "bold")
FONT_LAP = ("Consolas", 11)

TICK_MS = 33  # 刷新间隔（毫秒），约 30 帧


def flat_button(parent, **kw):
    """扁平风格按钮"""
    kw.setdefault("bd", 0)
    kw.setdefault("relief", "flat")
    kw.setdefault("cursor", "hand2")
    kw.setdefault("font", FONT_UI)
    kw.setdefault("activeforeground", kw.get("fg", TEXT))
    return tk.Button(parent, **kw)


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("计时器")
        root.configure(bg=BG)
        root.geometry("470x550")
        root.minsize(470, 550)

        # ---- 全局状态 ----
        self.mode = "countdown"          # countdown | stopwatch
        self.pinned = False

        # 倒计时状态
        self.cd_state = "idle"           # idle | running | paused | finished
        self.cd_remaining = 0.0
        self.cd_target = 0.0

        # 秒表状态
        self.sw_running = False
        self.sw_accum = 0.0
        self.sw_t0 = 0.0
        self.laps = []

        # 渲染缓存
        self._last_text = None
        self._last_status = None
        self._last_primary = None
        self._last_color = None

        self._build()
        self._bind_keys()
        self._tick()

    # ==================================================
    # 界面搭建
    # ==================================================
    def _build(self):
        root = self.root
        root.grid_rowconfigure(0, weight=0)
        root.grid_rowconfigure(1, weight=1)   # 时间显示（倒计时模式占满）
        root.grid_rowconfigure(2, weight=0)   # 模式内容（秒表模式占满）
        root.grid_rowconfigure(3, weight=0)
        root.grid_rowconfigure(4, weight=0)
        root.grid_columnconfigure(0, weight=1)

        # ---------- 顶栏：模式切换 + 置顶开关 ----------
        topbar = tk.Frame(root, bg=BG)
        topbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))

        bar = tk.Frame(topbar, bg=BG)
        bar.pack(fill="x")

        seg = tk.Frame(bar, bg=CARD)
        seg.pack(side="left")

        self.btn_cd = flat_button(
            seg, text="倒计时", width=8, pady=7, bg=ACCENT, fg="#FFFFFF",
            activebackground=ACCENT_HOVER, command=lambda: self._switch_mode("countdown"))
        self.btn_cd.pack(side="left")

        self.btn_sw = flat_button(
            seg, text="秒表", width=8, pady=7, bg=CARD, fg=MUTED,
            activebackground=CARD_HOVER, command=lambda: self._switch_mode("stopwatch"))
        self.btn_sw.pack(side="left")

        self.btn_pin = flat_button(
            bar, text="置顶", width=7, pady=7, bg=CARD, fg=MUTED,
            activebackground=CARD_HOVER, command=self._toggle_pin)
        self.btn_pin.pack(side="right")

        # 顶栏下的细分隔线
        tk.Frame(topbar, bg="#22262E", height=1).pack(fill="x", pady=(14, 0))

        # ---------- 时间显示 ----------
        disp = tk.Frame(root, bg=BG)
        disp.grid(row=1, column=0, sticky="nsew")

        self.lbl_time = tk.Label(
            disp, text="00:00:00", font=FONT_DIGIT, bg=BG, fg=TEXT)
        self.lbl_time.pack(expand=True)

        self.lbl_status = tk.Label(
            disp, text="准备就绪", font=FONT_SMALL, bg=BG, fg=MUTED)
        self.lbl_status.pack(pady=(0, 6))

        # ---------- 模式内容容器 ----------
        self.mode_box = tk.Frame(root, bg=BG)
        self.mode_box.grid(row=2, column=0, sticky="nsew", padx=16)

        self._build_countdown_box()
        self._build_stopwatch_box()
        self.sw_box.pack_forget()  # 默认显示倒计时

        # ---------- 操作按钮 ----------
        actions = tk.Frame(root, bg=BG)
        actions.grid(row=3, column=0, sticky="ew", padx=16, pady=(14, 0))

        bar = tk.Frame(actions, bg=BG)
        bar.pack(side="top")  # 让按钮组整体水平居中

        self.btn_lap = flat_button(
            bar, text="计次", width=8, pady=9, bg=CARD, fg=TEXT,
            activebackground=CARD_HOVER, command=self._lap)
        self.btn_lap.grid(row=0, column=0, padx=6)

        self.btn_primary = flat_button(
            bar, text="开始", width=10, pady=9, bg=ACCENT, fg="#FFFFFF",
            activebackground=ACCENT_HOVER, font=FONT_UI_BOLD,
            command=self._primary_action)
        self.btn_primary.grid(row=0, column=1, padx=6)

        self.btn_reset = flat_button(
            bar, text="重置", width=8, pady=9, bg=CARD, fg=MUTED,
            activebackground=CARD_HOVER, command=self._reset)
        self.btn_reset.grid(row=0, column=2, padx=6)

        self.btn_lap.grid_remove()  # 默认倒计时模式，隐藏「计次」

        # ---------- 底部快捷键提示 ----------
        tk.Label(
            root, text="空格 开始/暂停 · R 重置 · L 计次", font=FONT_SMALL,
            bg=BG, fg="#565C66").grid(row=4, column=0, sticky="ew", pady=(16, 12))

    def _build_countdown_box(self):
        self.cd_box = tk.Frame(self.mode_box, bg=BG)
        self.cd_box.pack(fill="x")

        # 时 / 分 / 秒 设置行
        row = tk.Frame(self.cd_box, bg=BG)
        row.pack(pady=(2, 10))

        self.cd_entries = []
        vcmd = (self.root.register(
            lambda s: s == "" or (s.isdigit() and len(s) <= 3)), "%P")

        for i, (label, default) in enumerate((("时", "0"), ("分", "0"), ("秒", "0"))):
            cell = tk.Frame(row, bg=BG)
            cell.pack(side="left", padx=12)

            ent = tk.Entry(
                cell, width=4, justify="center", font=FONT_SET,
                bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT, relief="flat",
                bd=0, highlightthickness=0, validate="key", validatecommand=vcmd)
            ent.insert(0, default)
            ent.pack()
            ent.bind("<KeyRelease>", lambda e: self._entries_changed())
            self.cd_entries.append(ent)

            tk.Label(cell, text=label, font=FONT_SMALL, bg=BG, fg=MUTED).pack(
                pady=(4, 0))

        # 快捷时长
        presets = tk.Frame(self.cd_box, bg=BG)
        presets.pack(pady=(0, 4))

        self.preset_buttons = []
        for text, m in (("1分钟", 1), ("5分钟", 5), ("10分钟", 10), ("25分钟", 25)):
            b = flat_button(
                presets, text=text, padx=12, pady=5, bg=CARD, fg=MUTED,
                activebackground=CARD_HOVER, font=FONT_SMALL,
                command=lambda mm=m: self._set_preset(mm))
            b.pack(side="left", padx=6)
            self.preset_buttons.append(b)

    def _build_stopwatch_box(self):
        self.sw_box = tk.Frame(self.mode_box, bg=BG)
        self.sw_box.pack(fill="both", expand=True)

        head = tk.Frame(self.sw_box, bg=BG)
        head.pack(fill="x", pady=(0, 6))
        tk.Label(head, text="计次记录", font=FONT_SMALL, bg=BG,
                 fg=MUTED).pack(side="left")
        self.lbl_lap_hint = tk.Label(head, text="运行后点击「计次」",
                                     font=FONT_SMALL, bg=BG, fg="#565C66")
        self.lbl_lap_hint.pack(side="right")

        card = tk.Frame(self.sw_box, bg=CARD)
        card.pack(fill="both", expand=True)

        self.lap_list = tk.Listbox(
            card, bg=CARD, fg=TEXT, font=FONT_LAP, bd=0, relief="flat",
            highlightthickness=0, selectbackground=ACCENT,
            selectborderwidth=0, activestyle="none", justify="left")
        self.lap_list.pack(side="left", fill="both", expand=True,
                           padx=10, pady=10)
        self.lap_list.bind(
            "<MouseWheel>",
            lambda e: self.lap_list.yview_scroll(-1 * (e.delta // 120), "units"))

    def _bind_keys(self):
        self.root.bind("<space>", self._on_space)
        self.root.bind("<r>", self._on_reset_key)
        self.root.bind("<R>", self._on_reset_key)
        self.root.bind("<l>", self._on_lap_key)
        self.root.bind("<L>", self._on_lap_key)

    @staticmethod
    def _typing(widget) -> bool:
        """焦点是否在输入控件上（避免快捷键冲突）"""
        return isinstance(widget, (tk.Entry, tk.Button, tk.Listbox))

    def _on_space(self, _event):
        if self._typing(self.root.focus_get()):
            return None
        self._primary_action()
        return "break"

    def _on_reset_key(self, _event):
        if self._typing(self.root.focus_get()):
            return None
        self._reset()
        return "break"

    def _on_lap_key(self, _event):
        if self._typing(self.root.focus_get()):
            return None
        if self.mode == "stopwatch":
            self._lap()
        return "break"

    # ==================================================
    # 模式切换 / 置顶
    # ==================================================
    def _switch_mode(self, mode):
        if mode == self.mode:
            return
        self.mode = mode
        if mode == "countdown":
            self.sw_box.pack_forget()
            self.cd_box.pack(fill="x")
            self.btn_lap.grid_remove()
            self.root.grid_rowconfigure(1, weight=1)
            self.root.grid_rowconfigure(2, weight=0)
            self.btn_cd.config(bg=ACCENT, fg="#FFFFFF", activebackground=ACCENT_HOVER)
            self.btn_sw.config(bg=CARD, fg=MUTED, activebackground=CARD_HOVER)
        else:
            self.cd_box.pack_forget()
            self.sw_box.pack(fill="both", expand=True)
            self.btn_lap.grid(row=0, column=0, padx=6)
            self.root.grid_rowconfigure(1, weight=0)
            self.root.grid_rowconfigure(2, weight=1)
            self.btn_sw.config(bg=ACCENT, fg="#FFFFFF", activebackground=ACCENT_HOVER)
            self.btn_cd.config(bg=CARD, fg=MUTED, activebackground=CARD_HOVER)
        self._render(force=True)

    def _toggle_pin(self):
        self.pinned = not self.pinned
        self.root.attributes("-topmost", self.pinned)
        if self.pinned:
            self.btn_pin.config(bg=ACCENT, fg="#FFFFFF", activebackground=ACCENT_HOVER)
        else:
            self.btn_pin.config(bg=CARD, fg=MUTED, activebackground=CARD_HOVER)

    # ==================================================
    # 倒计时
    # ==================================================
    def _parse_entries(self) -> int:
        total = 0
        for ent, factor in zip(self.cd_entries, (3600, 60, 1)):
            raw = ent.get().strip()
            total += (int(raw) if raw.isdigit() else 0) * factor
        return total

    def _entries_changed(self):
        if self.cd_state == "idle":
            self.cd_remaining = float(self._parse_entries())
            self._render(force=True)

    def _set_preset(self, minutes):
        if self.cd_state in ("running", "paused"):
            return
        values = ("0", str(minutes), "0")
        for ent, val in zip(self.cd_entries, values):
            ent.delete(0, "end")
            ent.insert(0, val)
        self._entries_changed()

    def _set_entries_editable(self, editable: bool):
        state = "normal" if editable else "disabled"
        for ent in self.cd_entries:
            ent.config(state=state,
                       disabledbackground=ENTRY_BG, disabledforeground=MUTED)
        for b in self.preset_buttons:
            if editable:
                b.config(state="normal", bg=CARD, fg=MUTED)
            else:
                b.config(state="disabled", bg="#121419", fg="#444A54")

    def _cd_toggle(self):
        now = time.monotonic()

        if self.cd_state in ("idle", "finished"):
            total = self._parse_entries()
            if total <= 0:
                messagebox.showwarning("计时器", "请先设置一个大于 0 的时间。")
                return
            self.cd_remaining = float(total)
            self.cd_target = now + self.cd_remaining
            self.cd_state = "running"
            self._set_entries_editable(False)

        elif self.cd_state == "running":
            self.cd_remaining = max(0.0, self.cd_target - now)
            self.cd_state = "paused"
            self._set_entries_editable(True)

        elif self.cd_state == "paused":
            self.cd_target = now + self.cd_remaining
            self.cd_state = "running"
            self._set_entries_editable(False)

    def _countdown_finished(self):
        if self.cd_state == "finished":
            return
        self.cd_state = "finished"
        self.cd_remaining = 0.0
        self._set_entries_editable(True)
        threading.Thread(target=self._alarm_sound, daemon=True).start()
        self.root.after(80, lambda: messagebox.showinfo(
            "计时器", "倒计时结束，时间到！"))

    @staticmethod
    def _alarm_sound():
        """到点提示音：三组叮咚声"""
        if winsound is None:
            return
        try:
            for _ in range(3):
                for freq in (880, 660, 880, 440):
                    winsound.Beep(freq, 180)
                    time.sleep(0.05)
                time.sleep(0.35)
        except Exception:
            pass

    # ==================================================
    # 秒表
    # ==================================================
    def _sw_elapsed(self) -> float:
        if self.sw_running:
            return self.sw_accum + (time.monotonic() - self.sw_t0)
        return self.sw_accum

    def _sw_toggle(self):
        if self.sw_running:
            self.sw_accum += time.monotonic() - self.sw_t0
            self.sw_running = False
        else:
            self.sw_t0 = time.monotonic()
            self.sw_running = True

    def _lap(self):
        if not self.sw_running:
            return
        elapsed = self._sw_elapsed()
        self.laps.append(elapsed)
        self.lap_list.insert(0, "#{:<3} {}".format(
            len(self.laps), self._fmt_sw(elapsed)))
        self.lap_list.selection_clear(0, "end")
        self.lbl_lap_hint.config(text="共 {} 次".format(len(self.laps)))

    # ==================================================
    # 主操作
    # ==================================================
    def _primary_action(self):
        if self.mode == "countdown":
            self._cd_toggle()
        else:
            self._sw_toggle()
        self._render(force=True)

    def _reset(self):
        if self.mode == "countdown":
            # 重置 = 彻底清零：状态、显示、输入框全部回到 00:00:00
            # 注意：必须先解锁输入框，禁用状态下程序写入会被 Tk 静默忽略
            self.cd_state = "idle"
            self._set_entries_editable(True)
            for ent in self.cd_entries:
                ent.delete(0, "end")
                ent.insert(0, "0")
            self.cd_remaining = 0.0
        else:
            self.sw_running = False
            self.sw_accum = 0.0
            self.laps.clear()
            self.lap_list.delete(0, "end")
            self.lbl_lap_hint.config(text="运行后点击「计次」")
        self._render(force=True)

    # ==================================================
    # 主循环
    # ==================================================
    def _tick(self):
        # 先安排下一次刷新，保证弹窗期间秒表照常走时
        self.root.after(TICK_MS, self._tick)

        now = time.monotonic()
        if self.cd_state == "running":
            self.cd_remaining = self.cd_target - now
            if self.cd_remaining <= 0:
                self._countdown_finished()
                self.cd_remaining = 0.0
        self._render()

    # ==================================================
    # 渲染
    # ==================================================
    @staticmethod
    def _fmt_cd(sec: float) -> str:
        total = max(0, int(math.ceil(sec - 1e-9)))
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return "{:02d}:{:02d}:{:02d}".format(h, m, s)

    @staticmethod
    def _fmt_sw(sec: float) -> str:
        cs = int(sec * 100) % 100
        s = int(sec) % 60
        m = int(sec // 60) % 60
        h = int(sec // 3600)
        if h:
            return "{}:{:02d}:{:02d}.{:02d}".format(h, m, s, cs)
        return "{:02d}:{:02d}.{:02d}".format(m, s, cs)

    def _status_info(self):
        if self.mode == "countdown":
            mapping = {
                "idle": ("准备就绪", MUTED),
                "running": ("倒计中", ACCENT),
                "paused": ("已暂停", MUTED),
                "finished": ("时间到！", WARN),
            }
            return mapping[self.cd_state]
        return ("计时中", ACCENT) if self.sw_running else \
               ("已暂停" if self.sw_accum else "准备就绪", MUTED)

    def _primary_text(self) -> str:
        if self.mode == "countdown":
            return {"idle": "开始", "running": "暂停",
                    "paused": "继续", "finished": "开始"}[self.cd_state]
        return "暂停" if self.sw_running else "开始"

    def _render(self, force=False):
        if self.mode == "countdown":
            text = self._fmt_cd(self.cd_remaining)
        else:
            text = self._fmt_sw(self._sw_elapsed())

        status, status_color = self._status_info()
        primary = self._primary_text()

        if force or text != self._last_text:
            self.lbl_time.config(text=text)
            self._last_text = text

        # 时间到 → 数字变琥珀色，直到再次开始
        color = WARN if (self.mode == "countdown" and
                         self.cd_state == "finished") else TEXT
        if force or color != self._last_color:
            self.lbl_time.config(fg=color)
            self._last_color = color

        if force or status != self._last_status:
            self.lbl_status.config(text=status, fg=status_color)
            self._last_status = status

        if force or primary != self._last_primary:
            self.btn_primary.config(text=primary)
            self._last_primary = primary


def resource_path(name):
    """资源路径：源码运行时在脚本旁，打包后在临时解包目录"""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(resource_path("icon.ico"))  # 标题栏 + 任务栏图标
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
