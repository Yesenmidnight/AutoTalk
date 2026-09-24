"""AutoTalk 主界面：桌面常驻置顶小挂件。"""

import queue
import re
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from . import analyzer, capture, ocr, winman
from .config import cfg
from .history import HistoryRecorder
from .picker import WindowListDialog, WindowRegionPicker

BG = "#191b22"
PANEL = "#212430"
CARD_BG = "#272a38"
CARD_HOVER = "#323748"
CARD_COPIED = "#1e3b30"
FG = "#e8eaf2"
SUB = "#8f99ad"
ACCENT = "#7aa2f7"
ACCENT_GREEN = "#73daca"
ACCENT_ORANGE = "#ff9e64"
ACCENT_PURPLE = "#bb9af7"
BTN = "#2f3444"
BTN_HOT = "#3b4256"

FONT = ("Microsoft YaHei UI", 10)
FONT_B = ("Microsoft YaHei UI", 10, "bold")
FONT_S = ("Microsoft YaHei UI", 9)
FONT_XS = ("Microsoft YaHei UI", 8)
FONT_CARD_CONTENT = ("Microsoft YaHei UI", 10)

TAG_STYLES = {
    "稳妥": {"bg": "#1e3a5f", "fg": "#7aa2f7"},
    "进取": {"bg": "#4a2d1d", "fg": "#ff9e64"},
    "试探": {"bg": "#3a254e", "fg": "#bb9af7"},
    "恭敬": {"bg": "#1b3c2f", "fg": "#73daca"},
    "直接": {"bg": "#441d24", "fg": "#f7768e"},
    "默认": {"bg": "#252e3d", "fg": "#7dcfff"},
}


class ReplyCard(tk.Frame):
    """独立推荐回复卡片组件：支持策略标签显示、台词展示、预期说明与一键复制。"""

    def __init__(self, master, reply_data, on_copy=None):
        super().__init__(master, bg=CARD_BG, relief="flat", bd=0, padx=10, pady=7)
        self.reply_data = reply_data
        self.on_copy = on_copy
        self._copied_timer = None
        self._interactive_widgets = []

        tag = reply_data.get("tag", "推荐")
        idx = reply_data.get("index", 1)
        style = TAG_STYLES.get(tag, TAG_STYLES["默认"])

        # 顶部栏：编号 + 策略标签 + 预期效果 + 右侧复制按钮
        self.top_row = tk.Frame(self, bg=CARD_BG)
        self.top_row.pack(fill="x", pady=(0, 4))

        self.idx_badge = tk.Label(
            self.top_row, text=" %s " % idx, bg=style["bg"], fg=style["fg"],
            font=("Microsoft YaHei UI", 8, "bold"), bd=0
        )
        self.idx_badge.pack(side="left", padx=(0, 6))

        self.tag_lbl = tk.Label(
            self.top_row, text="【%s】" % tag, bg=CARD_BG, fg=style["fg"],
            font=("Microsoft YaHei UI", 9, "bold"), bd=0
        )
        self.tag_lbl.pack(side="left")

        expected = reply_data.get("expected", "")
        if expected:
            self.exp_lbl = tk.Label(
                self.top_row, text="预期：%s" % expected, bg=CARD_BG, fg=SUB,
                font=FONT_XS, anchor="w"
            )
            self.exp_lbl.pack(side="left", padx=(6, 0), fill="x", expand=True)
        else:
            self.exp_lbl = None

        self.copy_btn = tk.Button(
            self.top_row, text="📋 复制", command=self.do_copy,
            bg=BTN, fg=FG, activebackground=BTN_HOT, activeforeground=FG,
            relief="flat", bd=0, padx=8, pady=1, font=FONT_XS, cursor="hand2"
        )
        self.copy_btn.pack(side="right", padx=(4, 0))

        # 中部栏：纯台词内容（用于直接粘贴到游戏）
        self.mid_row = tk.Frame(self, bg=CARD_BG)
        self.mid_row.pack(fill="x", pady=(2, 0))

        content = reply_data.get("content", "")
        self.content_lbl = tk.Label(
            self.mid_row, text=content, bg=CARD_BG, fg=FG,
            font=FONT_CARD_CONTENT, wraplength=380, justify="left", anchor="w"
        )
        self.content_lbl.pack(fill="x", expand=True)

        # 收集需要响应悬停和点击复制的容器及组件
        self._interactive_widgets = [
            self, self.top_row, self.mid_row, self.tag_lbl, self.content_lbl
        ]
        if self.exp_lbl:
            self._interactive_widgets.append(self.exp_lbl)

        for w in self._interactive_widgets:
            w.configure(cursor="hand2")
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", lambda e: self.do_copy())

    def update_wrap(self, total_width):
        """随容器宽度自适应调整正文换行宽度。"""
        wrap = max(220, int(total_width) - 40)
        self.content_lbl.configure(wraplength=wrap)

    def _set_bg_color(self, color):
        self.configure(bg=color)
        self.top_row.configure(bg=color)
        self.mid_row.configure(bg=color)
        self.tag_lbl.configure(bg=color)
        self.content_lbl.configure(bg=color)
        if self.exp_lbl:
            self.exp_lbl.configure(bg=color)

    def _on_enter(self, _event=None):
        if not self._copied_timer:
            self._set_bg_color(CARD_HOVER)

    def _on_leave(self, _event=None):
        if not self._copied_timer:
            self._set_bg_color(CARD_BG)

    def do_copy(self):
        content = self.reply_data.get("content", "")
        if self.on_copy:
            self.on_copy(content, self.reply_data)

        # 视觉反馈：按钮绿亮，卡片高亮
        self.copy_btn.configure(text="✓ 已复制", bg=ACCENT_GREEN, fg="#1a1c23")
        self._set_bg_color(CARD_COPIED)

        if self._copied_timer:
            self.after_cancel(self._copied_timer)

        def reset():
            self._copied_timer = None
            self.copy_btn.configure(text="📋 复制", bg=BTN, fg=FG)
            self._on_leave()

        self._copied_timer = self.after(1400, reset)

# 中文输入法下按 ` 键常产生全角/间隔号字符，统一映射回 keyboard 库认识的键名
KEY_ALIASES = {"·": "`", "｀": "`", "‵": "`", "‘": "'", "’": "'",
               "，": ",", "。": "."}
API_PRESETS = [
    "https://open.bigmodel.cn/api/coding/paas/v4",
    "https://open.bigmodel.cn/api/paas/v4",
    "https://api.deepseek.com",
    "https://api.moonshot.cn/v1",
    "https://api.openai.com/v1",
]
MODEL_PRESETS = ["deepseek-flash", "deepseek-v4-pro", "glm-5.3-flash", "glm-4.6", "deepseek-chat"]


def _normalize(text):
    return "".join(text.split())


def _hotkey_label(hotkey):
    return "+".join(p.capitalize() for p in hotkey.split("+"))


def _normalize_hotkey(hotkey):
    parts = [p.strip().lower() for p in (hotkey or "").split("+") if p.strip()]
    return "+".join(KEY_ALIASES.get(p, p) for p in parts)


class HotkeyRecorder(tk.Frame):
    """快捷键录入控件：点「录入」后按下组合键即可，无需手敲键名。"""

    MODS = {"control_l": "ctrl", "control_r": "ctrl", "control": "ctrl",
            "shift_l": "shift", "shift_r": "shift", "shift": "shift",
            "alt_l": "alt", "alt_r": "alt", "alt": "alt",
            "win_l": "windows", "win_r": "windows", "super_l": "windows"}
    MOD_ORDER = ["ctrl", "shift", "alt", "windows"]

    def __init__(self, master, value):
        super().__init__(master, bg=BG)
        self.var = tk.StringVar(value=value)
        tk.Entry(self, textvariable=self.var, bg=PANEL, fg=FG, relief="flat",
                 width=20, state="readonly", readonlybackground=PANEL,
                 font=FONT_S).pack(side="left")
        self.btn = tk.Button(self, text="录入", command=self._start, bg=BTN, fg=FG,
                             activebackground=BTN_HOT, activeforeground=FG,
                             relief="flat", bd=0, padx=8, pady=2, font=FONT_S,
                             cursor="hand2")
        self.btn.pack(side="left", padx=(6, 0))
        self._recording = False
        self._mods = set()

    def _start(self):
        self._recording = True
        self._mods = set()
        self.btn.configure(text="请按键…", bg=ACCENT, fg="#1b1d24")
        top = self.winfo_toplevel()
        top.bind("<KeyPress>", self._on_press)
        top.bind("<KeyRelease>", self._on_release)

    def _on_press(self, event):
        if not self._recording:
            return
        name = event.keysym.lower()
        if name == "escape":
            self._stop(None)
        elif name in self.MODS:
            self._mods.add(self.MODS[name])
        else:
            # 可打印字符（如 `、1、a）直接用字符作为键名，与 keyboard 库一致
            key = event.char if event.char and event.char.isprintable() \
                and event.char not in " " else name
            mods = [m for m in self.MOD_ORDER if m in self._mods]
            self._stop("+".join(mods + [KEY_ALIASES.get(key, key)]))

    def _on_release(self, event):
        if self._recording and event.keysym.lower() in self.MODS:
            self._mods.discard(self.MODS[event.keysym.lower()])

    def _stop(self, combo):
        self._recording = False
        top = self.winfo_toplevel()
        top.unbind("<KeyPress>")
        top.unbind("<KeyRelease>")
        self.btn.configure(text="录入", bg=BTN, fg=FG)
        if combo:
            self.var.set(combo)


def _hotkey_label(hotkey):
    return "+".join(p.capitalize() for p in hotkey.split("+"))


def _clip_region(region, client):
    """把保存的相对区域裁剪到当前窗口客户区内，窗口尺寸变化时自动兜底。"""
    ix1 = max(0, int(region["x"]))
    iy1 = max(0, int(region["y"]))
    ix2 = min(int(client["w"]), int(region["x"]) + int(region["w"]))
    iy2 = min(int(client["h"]), int(region["y"]) + int(region["h"]))
    if ix2 - ix1 < 30 or iy2 - iy1 < 16:
        raise RuntimeError("对话区域已超出游戏窗口，请重新「框选对话区」")
    return {"x": ix1, "y": iy1, "w": ix2 - ix1, "h": iy2 - iy1}


class AutoTalkApp:
    def __init__(self):
        self.cfg = cfg
        self.root = tk.Tk()
        self.root.title("AutoTalk · 不问凡尘 对话助手")
        self.root.geometry("480x740")
        self.root.minsize(440, 620)
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self._topmost = True

        self.queue = queue.Queue()
        self._busy = False
        self._busy_lock = threading.Lock()
        self._watch_on = False
        self._last_watch_norm = ""
        self.history = []
        self.reply_cards = []
        self.history_recorder = HistoryRecorder()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._poll)
        self._register_hotkey()
        self._update_win_label()
        self.root.bind("<Key>", self._on_key_press)

        if not self.cfg.get("window"):
            self._status("首次使用：请先点「选游戏窗口」，再框选对话区域")
        elif not self.cfg.get("region"):
            self._status("请点「框选对话区」框住游戏中的对话窗口")
        else:
            self._status("就绪（支持点击推荐回复或按数字键 1/2/3 复制）")
        if self._hotkey_error:
            self._status(self._hotkey_error)

    # ---------- 界面 ----------

    def _mk_btn(self, parent, text, cmd, **kw):
        return tk.Button(
            parent, text=text, command=cmd, bg=kw.get("bg", BTN),
            fg=kw.get("fg", FG), activebackground=BTN_HOT,
            activeforeground=FG, relief="flat", bd=0, padx=9, pady=3,
            font=FONT_S, cursor="hand2",
        )

    def _build_ui(self):
        # 1. 顶部操作栏
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=8, pady=(8, 2))

        self.btn_window = self._mk_btn(bar, "选游戏窗口", self._pick_window)
        self.btn_window.pack(side="left")
        self.btn_region = self._mk_btn(bar, "框选对话区", self._pick_region)
        self.btn_region.pack(side="left", padx=(6, 0))
        self.btn_watch = self._mk_btn(bar, "自动·关", self._toggle_watch)
        self.btn_watch.pack(side="left", padx=(6, 0))
        self._mk_btn(bar, "清空", self._clear_all).pack(side="left", padx=(6, 0))
        self._mk_btn(bar, "历史", self._open_history).pack(side="left", padx=(6, 0))
        self._mk_btn(bar, "设置", self._open_settings).pack(side="left", padx=(6, 0))
        self.btn_pin = self._mk_btn(bar, "📌 已置顶", self._toggle_pin)
        self.btn_pin.pack(side="right")

        # 2. 状态标签
        self.win_label = tk.Label(self.root, text="", bg=BG, fg=SUB,
                                  anchor="w", font=FONT_S)
        self.win_label.pack(fill="x", padx=10, pady=(0, 2))

        # 3. 抓取大按钮
        self.btn_capture = self._mk_btn(self.root, self._capture_label(), self.on_capture)
        self.btn_capture.pack(fill="x", padx=10, pady=(2, 4))

        # 4. 识别文本区（紧凑 3 行，右上角带重新分析按钮）
        ocr_head = tk.Frame(self.root, bg=BG)
        ocr_head.pack(fill="x", padx=10, pady=(3, 1))
        tk.Label(ocr_head, text="识别文本（可手动编辑微调）", bg=BG, fg=SUB,
                 anchor="w", font=FONT_S).pack(side="left")
        self.btn_reanalyze = self._mk_btn(
            ocr_head, "🔄 重新分析", self._do_analyze,
            bg="#2c3345", padx=8, pady=1
        )
        self.btn_reanalyze.pack(side="right")

        self.ocr_box = scrolledtext.ScrolledText(
            self.root, height=3, font=FONT, bg=PANEL, fg=FG,
            insertbackground=FG, relief="flat", wrap="word")
        self.ocr_box.pack(fill="x", padx=10, pady=(2, 4))

        # 5. 中间：局势与 NPC 洞察区（只呈现性格、动机与线索分析，不再堆积回复）
        tk.Label(self.root, text="💡 局势与 NPC 洞察（性格/情绪/意图）", bg=BG, fg=SUB,
                 anchor="w", font=FONT_S).pack(fill="x", padx=10, pady=(3, 1))
        self.insight_box = scrolledtext.ScrolledText(
            self.root, height=5, state="disabled", font=FONT, bg=PANEL, fg=FG,
            relief="flat", wrap="word")
        self.insight_box.pack(fill="x", padx=10, pady=(2, 4))
        self.insight_box.tag_configure("head", foreground=ACCENT, font=FONT_B)
        self.insight_box.tag_configure("dim", foreground=SUB)
        self.insight_box.tag_configure("err", foreground="#f7768e")

        # 6. 下方：专属独立的推荐回复区域（卡片化，支持滚轮滚动与一键复制）
        reply_head = tk.Frame(self.root, bg=BG)
        reply_head.pack(fill="x", padx=10, pady=(5, 2))
        tk.Label(
            reply_head, text="💬 推荐回复", bg=BG, fg=ACCENT,
            anchor="w", font=FONT_B
        ).pack(side="left")
        tk.Label(
            reply_head, text="（点击卡片或复制按钮复制台词，按数字键 1/2/3 亦可）",
            bg=BG, fg=SUB, anchor="w", font=FONT_XS
        ).pack(side="left", padx=(4, 0))

        reply_container = tk.Frame(self.root, bg=BG)
        reply_container.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        self.reply_canvas = tk.Canvas(reply_container, bg=BG, highlightthickness=0, bd=0)
        self.reply_scroll = ttk.Scrollbar(reply_container, orient="vertical", command=self.reply_canvas.yview)
        self.reply_canvas.configure(yscrollcommand=self.reply_scroll.set)

        self.reply_scroll.pack(side="right", fill="y")
        self.reply_canvas.pack(side="left", fill="both", expand=True)

        self.reply_inner = tk.Frame(self.reply_canvas, bg=BG)
        self.reply_canvas_win = self.reply_canvas.create_window((0, 0), window=self.reply_inner, anchor="nw")

        self.reply_canvas.bind("<Configure>", self._on_canvas_configure)
        self.reply_inner.bind("<Configure>", lambda e: self.reply_canvas.configure(
            scrollregion=self.reply_canvas.bbox("all")
        ))

        self._bind_mousewheel(self.reply_canvas)
        self._bind_mousewheel(self.reply_inner)

        self.reply_placeholder = tk.Label(
            self.reply_inner, text="暂无推荐回复\n抓取对话或重新分析后生成可直接复制的回复",
            bg=BG, fg=SUB, font=FONT_S, pady=36, justify="center"
        )
        self.reply_placeholder.pack(fill="x", expand=True)

        # 7. 底部状态栏
        self.status = tk.Label(self.root, text="", bg=BG, fg=SUB, anchor="w", font=FONT_S)
        self.status.pack(fill="x", padx=10, pady=(0, 6))

    def _on_canvas_configure(self, event):
        canvas_w = event.width
        self.reply_canvas.itemconfig(self.reply_canvas_win, width=canvas_w)
        for card in self.reply_cards:
            card.update_wrap(canvas_w)

    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)

    def _bind_mousewheel_recursive(self, widget):
        self._bind_mousewheel(widget)
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _on_mousewheel(self, event):
        if self.reply_canvas.winfo_exists():
            self.reply_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_key_press(self, event):
        # 若焦点在可编辑文本框中，不拦截数字键
        if self.root.focus_get() == self.ocr_box:
            return
        if event.char and event.char.isdigit():
            idx = int(event.char)
            if 1 <= idx <= len(self.reply_cards):
                self.reply_cards[idx - 1].do_copy()

    def _capture_label(self):
        return "抓取分析 " + _hotkey_label(self.cfg.get("hotkey", ""))

    def _status(self, msg):
        self.status.configure(text=msg)

    def _update_win_label(self):
        spec = self.cfg.get("window")
        region = self.cfg.get("region")
        if not spec:
            text = "游戏窗口：未设置"
        else:
            title = spec.get("title", "")
            if len(title) > 24:
                title = title[:23] + "…"
            text = "游戏窗口：%s (%s)" % (title, spec.get("exe") or "?")
            if region:
                text += " ｜ 对话区 %d×%d（相对窗口）" % (region["w"], region["h"])
            else:
                text += " ｜ 对话区未框选"
        hotkey = self.cfg.get("hotkey", "")
        if hotkey:
            text += " ｜ 快捷键 %s%s" % (
                _hotkey_label(hotkey), "✗" if self._hotkey_error else " ✓")
        self.win_label.configure(text=text)

    # ---------- 事件轮询（工作线程 -> UI）----------

    def _poll(self):
        try:
            while True:
                ev = self.queue.get_nowait()
                kind = ev[0]
                if kind == "hotkey":
                    self.on_capture()
                elif kind == "ocr":
                    self._on_ocr(ev[1], ev[2])
                elif kind == "analysis":
                    self._set_result(ev[1])
                    self._status("完成 ✓")
                elif kind == "error":
                    self._set_error(ev[1])
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _try_busy(self):
        with self._busy_lock:
            if self._busy:
                return False
            self._busy = True
            return True

    def _release_busy(self):
        with self._busy_lock:
            self._busy = False

    # ---------- 抓取 + OCR ----------

    def on_capture(self):
        if not self.cfg.get("window"):
            self._status("请先点「选游戏窗口」指定游戏窗口")
            return
        if not self.cfg.get("region"):
            self._status("请先点「框选对话区」框住对话窗口")
            return
        if not self._try_busy():
            self._status("正在处理中，请稍候…")
            return
        self._status("截图 + OCR 识别中…")
        threading.Thread(target=self._capture_work, args=(False,), daemon=True).start()

    def _auto_capture(self):
        if not self._try_busy():
            return
        threading.Thread(target=self._capture_work, args=(True,), daemon=True).start()

    def _capture_work(self, auto):
        try:
            client = winman.get_client_box(self.cfg.get("window"))
            clipped = _clip_region(self.cfg.get("region"), client)
            abs_region = {
                "x": client["x"] + clipped["x"],
                "y": client["y"] + clipped["y"],
                "w": clipped["w"],
                "h": clipped["h"],
            }
            img = capture.grab_region(abs_region)
            if self.cfg.get("save_captures"):
                capture.save_capture(img)
            text = ocr.recognize(img)
            self.queue.put(("ocr", text, auto))
        except Exception as e:
            self.queue.put(("error", "抓取失败：%s" % e))
        finally:
            self._release_busy()

    def _on_ocr(self, text, auto):
        self.ocr_box.delete("1.0", "end")
        self.ocr_box.insert("1.0", text)
        if not text.strip():
            self._status("未识别到文字：请确认框选区域覆盖了对话内容")
            return
        if auto:
            norm = _normalize(text)
            if norm == self._last_watch_norm:
                self._status("监听中…（内容未变化）")
                return
            self._last_watch_norm = norm
        self._do_analyze()

    # ---------- AI 分析 ----------

    def _do_analyze(self):
        if not self._try_busy():
            self._status("正在处理中，请稍候…")
            return
        current = self.ocr_box.get("1.0", "end").strip()
        if not current:
            self._release_busy()
            self._status("没有可分析的对话内容")
            return

        # 避免重复向历史记录追加相同的当前对话（如重复点击「重新分析」）
        norm_cur = _normalize(current)
        if not self.history or _normalize(self.history[-1]) != norm_cur:
            self.history.append(current)
        limit = max(2, int(self.cfg.get("history_limit", 6)))
        self.history = self.history[-limit:]
        hist = [h for h in self.history if _normalize(h) != norm_cur]
        self._status("AI 分析中…（通常 3~15 秒）")

        def work():
            try:
                reply = analyzer.analyze(hist, current)
                self.queue.put(("analysis", reply))
            except Exception as e:
                self.queue.put(("error", "分析失败：%s" % e))
            finally:
                self._release_busy()

        threading.Thread(target=work, daemon=True).start()

    def _set_result(self, text):
        if not text or not text.strip():
            self._set_error("大模型未返回有效正文（返回为空），请点击「🔄 重新分析」重试")
            return

        parsed = analyzer.parse_analysis(text)
        insights = parsed.get("insights", "")
        replies = parsed.get("replies", [])
        if not insights.strip():
            # 兜底：若分段未匹配，展示完整大模型输出文本，绝不让用户看到空文本框
            insights = text.strip()

        # 1. 渲染局势与 NPC 洞察区
        box = self.insight_box
        box.configure(state="normal")
        box.delete("1.0", "end")
        for line in (insights or "").splitlines():
            stripped = line.strip()
            if not stripped:
                box.insert("end", "\n")
                continue
            if stripped.startswith("【") and "】" in stripped and len(stripped) <= 20:
                box.insert("end", stripped + "\n", "head")
            else:
                box.insert("end", stripped + "\n")
        box.configure(state="disabled")

        # 2. 渲染专属推荐回复卡片列表
        for card in self.reply_cards:
            card.destroy()
        self.reply_cards.clear()

        if replies:
            self.reply_placeholder.pack_forget()
            canvas_w = self.reply_canvas.winfo_width()
            for r_data in replies:
                card = ReplyCard(self.reply_inner, r_data, on_copy=self._on_copy_reply)
                card.pack(fill="x", pady=3)
                if canvas_w > 50:
                    card.update_wrap(canvas_w)
                self._bind_mousewheel_recursive(card)
                self.reply_cards.append(card)
        else:
            self.reply_placeholder.configure(text="未能提取到结构化推荐回复，请参考上方洞察内容")
            self.reply_placeholder.pack(fill="x", expand=True)

        self.reply_canvas.yview_moveto(0)

        # 归档至当前打开时间戳命名的 Markdown 文件
        ocr_text = self.ocr_box.get("1.0", "end").strip()
        self.history_recorder.record_turn(ocr_text, insights, replies)

    def _open_history(self):
        self.history_recorder.open_folder()
        self._status("已在资源管理器中打开历史记录文件夹: history/")

    def _on_copy_reply(self, content, reply_data):
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        tag = reply_data.get("tag", "推荐")
        preview = content if len(content) <= 32 else content[:32] + "…"
        self._status("已复制【%s】：%s" % (tag, preview))
        self.history_recorder.record_copy(reply_data)

    def _set_error(self, msg):
        box = self.insight_box
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", msg, "err")
        box.configure(state="disabled")

        for card in self.reply_cards:
            card.destroy()
        self.reply_cards.clear()
        self.reply_placeholder.configure(text="分析异常，详见上方红字提示")
        self.reply_placeholder.pack(fill="x", expand=True)
        self._status("出错了，详见上方红字")

    # ---------- 自动监听 ----------

    def _toggle_watch(self):
        self._watch_on = not self._watch_on
        if self._watch_on:
            if not self.cfg.get("window") or not self.cfg.get("region"):
                self._watch_on = False
                self._status("请先设置游戏窗口并框选对话区，再开启自动监听")
            else:
                self._last_watch_norm = ""
                self.btn_watch.configure(
                    text="自动·开(%ss)" % int(float(self.cfg.get("watch_interval_sec", 3))),
                    bg=ACCENT, fg="#1b1d24")
                self._watch_tick()
        else:
            self.btn_watch.configure(text="自动·关", bg=BTN, fg=FG)
            self._status("自动监听已关闭")

    def _watch_tick(self):
        if not self._watch_on:
            return
        if not self._busy and self.cfg.get("region"):
            self._auto_capture()
        interval = max(0.5, float(self.cfg.get("watch_interval_sec", 3)))
        self.root.after(int(interval * 1000), self._watch_tick)

    # ---------- 游戏窗口与区域 ----------

    def _pick_window(self):
        try:
            WindowListDialog(self.root, on_select=self._on_window_selected)
        except Exception as e:
            self._status("窗口列表失败：%s" % e)

    def _on_window_selected(self, spec):
        self.cfg["window"] = spec
        self.cfg["region"] = None
        self.cfg.save()
        self._update_win_label()
        self._status("游戏窗口已选定，接下来在弹出的窗口画面上框选对话区域")
        self.root.after(150, self._pick_region)

    def _pick_region(self):
        spec = self.cfg.get("window")
        if not spec:
            self._status("请先点「选游戏窗口」指定游戏窗口")
            return
        try:
            box = winman.get_client_box(spec)
            img = capture.grab_region(box)
        except Exception as e:
            self._status("框选失败：%s" % e)
            return
        try:
            WindowRegionPicker(
                self.root, img, box,
                on_save=self._on_region,
                on_cancel=lambda: self._status("已取消框选"),
            )
        except Exception as e:
            self._status("框选失败：%s" % e)

    def _on_region(self, region):
        self.cfg["region"] = region
        self.cfg.save()
        self._update_win_label()
        self._status("对话区域已保存：%d×%d（相对游戏窗口），按快捷键即可抓取"
                     % (region["w"], region["h"]))

    # ---------- 快捷键 ----------

    def _on_hotkey(self):
        self.queue.put(("hotkey",))

    def _register_hotkey(self):
        self._hotkey_error = None
        try:
            import keyboard
        except ImportError:
            self._hotkey_error = "未安装 keyboard 库，快捷键不可用（pip install keyboard）"
            return
        try:
            keyboard.unhook_all()
            hotkey = _normalize_hotkey(self.cfg.get("hotkey", ""))
            self.cfg["hotkey"] = hotkey
            if hotkey:
                keyboard.add_hotkey(hotkey, self._on_hotkey)
        except Exception as e:
            self._hotkey_error = ("快捷键「%s」注册失败：%s，请到「设置」重新录入"
                                  % (self.cfg.get("hotkey", ""), e))

    # ---------- 设置 ----------

    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("设置")
        win.configure(bg=BG, padx=14, pady=12)
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        entries = {}

        def add_label(row, text):
            tk.Label(win, text=text, bg=BG, fg=SUB, font=FONT_S).grid(
                row=row, column=0, sticky="w", pady=4)

        def add_entry(row, key, show=""):
            var = tk.StringVar(value=str(self.cfg.get(key, "")))
            ent = tk.Entry(win, textvariable=var, bg=PANEL, fg=FG,
                           insertbackground=FG, relief="flat", width=36)
            if show:
                ent.configure(show=show)
            ent.grid(row=row, column=1, padx=(10, 0), pady=4)
            entries[key] = var
            return var

        add_label(0, "API 地址")
        api_var = add_entry(0, "api_base")
        ttk.Combobox(win, values=API_PRESETS, textvariable=api_var,
                     state="normal", width=36).grid(row=1, column=1,
                                                    padx=(10, 0), pady=(0, 2))
        tk.Label(win, text="↑ Coding Plan 订阅 Key 选第 1 个；按量付费 Key 选第 2 个",
                 bg=BG, fg=SUB, font=FONT_S, anchor="w").grid(
            row=2, column=0, columnspan=2, sticky="w")
        add_label(3, "API Key")
        add_entry(3, "api_key", show="*")
        add_label(4, "模型")
        model_var = add_entry(4, "model")
        ttk.Combobox(win, values=MODEL_PRESETS, textvariable=model_var,
                     state="normal", width=36).grid(row=5, column=1,
                                                    padx=(10, 0), pady=(0, 4))
        add_label(6, "快捷键")
        recorder = HotkeyRecorder(win, self.cfg.get("hotkey", ""))
        recorder.grid(row=6, column=1, padx=(10, 0), pady=4, sticky="w")
        add_label(7, "监听间隔（秒）")
        add_entry(7, "watch_interval_sec")

        row = 8
        sc_var = tk.BooleanVar(value=bool(self.cfg.get("save_captures", False)))
        tk.Checkbutton(win, text="保存每次截图到 captures/（排查识别问题用）",
                       variable=sc_var, bg=BG, fg=FG, activebackground=BG,
                       activeforeground=FG, selectcolor=PANEL, font=FONT_S
                       ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(6, 2))

        btns = tk.Frame(win, bg=BG)
        btns.grid(row=row + 1, column=0, columnspan=2, pady=(10, 0))

        def save():
            self.cfg["api_base"] = api_var.get().strip()
            self.cfg["api_key"] = entries["api_key"].get().strip()
            self.cfg["model"] = model_var.get().strip()
            hotkey = _normalize_hotkey(recorder.var.get())
            if hotkey:
                try:
                    import keyboard
                    for part in hotkey.split("+"):
                        keyboard.key_to_scan_codes(part)
                except Exception as e:
                    messagebox.showerror(
                        "快捷键无效",
                        "「%s」无法注册：%s\n\n请点「录入」重新按下组合键，"
                        "例如 Ctrl+Alt+T、F8、Ctrl+`" % (hotkey, e))
                    return
            self.cfg["hotkey"] = hotkey
            try:
                self.cfg["watch_interval_sec"] = float(entries["watch_interval_sec"].get())
            except ValueError:
                pass
            self.cfg["save_captures"] = bool(sc_var.get())
            self.cfg.save()
            self._register_hotkey()
            self._update_win_label()
            self.btn_capture.configure(text=self._capture_label())
            self._status("设置已保存" + ("（注意：%s）" % self._hotkey_error
                                      if self._hotkey_error else ""))
            win.destroy()

        self._mk_btn(btns, "保存", save).pack(side="left", padx=4)
        self._mk_btn(btns, "取消", win.destroy).pack(side="left", padx=4)

    # ---------- 其他 ----------

    def _clear_all(self):
        self.ocr_box.delete("1.0", "end")
        self.insight_box.configure(state="normal")
        self.insight_box.delete("1.0", "end")
        self.insight_box.configure(state="disabled")

        for card in self.reply_cards:
            card.destroy()
        self.reply_cards.clear()
        self.reply_placeholder.configure(text="暂无推荐回复\n抓取对话或重新分析后生成可直接复制的回复")
        self.reply_placeholder.pack(fill="x", expand=True)

        self.history.clear()
        self._last_watch_norm = ""
        self._status("已清空（含本轮对话历史）")

    def _toggle_pin(self):
        self._topmost = not self._topmost
        self.root.attributes("-topmost", self._topmost)
        self.btn_pin.configure(text="📌 已置顶" if self._topmost else "📌 未置顶")

    def _on_close(self):
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()
