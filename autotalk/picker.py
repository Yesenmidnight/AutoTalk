"""窗口选择列表 + 在冻结的游戏窗口画面上框选对话区域。"""

import tkinter as tk
from tkinter import ttk

from PIL import ImageTk

from . import winman
from .config import cfg

BG = "#1e2027"
PANEL = "#262933"
FG = "#e8eaf0"
SUB = "#98a0b0"
ACCENT = "#7aa2f7"
BTN = "#333846"
BTN_HOT = "#3d4354"
FONT = ("Microsoft YaHei UI", 10)
FONT_S = ("Microsoft YaHei UI", 9)

REGION_HINT = "按住鼠标拖动，框选游戏对话窗口区域（松开即保存，Esc 取消）"


class WindowListDialog(tk.Toplevel):
    """列出系统窗口，让用户指定哪一个是游戏窗口。"""

    def __init__(self, master, on_select):
        super().__init__(master)
        self.on_select = on_select
        self.windows = []
        self.title("选择游戏窗口")
        self.configure(bg=BG, padx=12, pady=10)
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)

        tip = tk.Label(self, text="请选择游戏所在的窗口（双击即选定）：",
                       bg=BG, fg=FG, font=FONT, anchor="w")
        tip.pack(fill="x", pady=(0, 4))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(body, width=72, height=16, bg=PANEL, fg=FG,
                                  selectbackground=ACCENT, selectforeground="#1b1d24",
                                  relief="flat", highlightthickness=0,
                                  font=("Microsoft YaHei UI", 9), activestyle="none")
        sb = ttk.Scrollbar(body, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.listbox.bind("<Double-Button-1>", lambda _e: self._confirm())

        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", pady=(8, 0))
        self._mk_btn(btns, "刷新列表", self.refresh).pack(side="left", padx=4)
        self._mk_btn(btns, "选定", self._confirm).pack(side="left", padx=4)
        self._mk_btn(btns, "取消", self.destroy).pack(side="left", padx=4)

        self.current_spec = cfg.get("window")
        self.refresh()

    def _mk_btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, bg=BTN, fg=FG,
                         activebackground=BTN_HOT, activeforeground=FG,
                         relief="flat", bd=0, padx=10, pady=3, font=FONT_S,
                         cursor="hand2")

    def refresh(self):
        self.windows = winman.list_windows()
        current = self.current_spec or {}
        self.listbox.delete(0, "end")
        select_index = None
        for i, w in enumerate(self.windows):
            title = w["title"] if len(w["title"]) <= 42 else w["title"][:41] + "…"
            self.listbox.insert("end", "%s   [%s]  %d×%d"
                                % (title, w["exe"] or "?", w["box"]["w"], w["box"]["h"]))
            if (current.get("title") == w["title"]
                    and (current.get("exe") or "") == w["exe"]):
                select_index = i
        if select_index is not None:
            self.listbox.selection_set(select_index)
            self.listbox.see(select_index)

    def _confirm(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        w = self.windows[sel[0]]
        spec = {"title": w["title"], "exe": w["exe"]}
        self.destroy()
        self.on_select(spec)


class WindowRegionPicker(tk.Toplevel):
    """冻结游戏窗口画面，在其上拖拽框选对话区域。

    img: 游戏窗口客户区的截图；box: 该客户区的屏幕绝对坐标。
    保存的是相对客户区的坐标，窗口移动/换显示器后依然有效。
    """

    def __init__(self, master, img, box, on_save, on_cancel=None):
        super().__init__(master)
        self._box = box
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="black", cursor="crosshair")
        self.geometry("%dx%d+%d+%d" % (box["w"], box["h"], box["x"], box["y"]))

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, image=self._photo, anchor="nw")
        self.canvas.create_rectangle(0, 0, box["w"], 40, fill="#000000",
                                     stipple="gray50", outline="")
        self._hint_id = self.canvas.create_text(
            box["w"] // 2, 20, text=REGION_HINT, fill="#ffffff",
            font=("Microsoft YaHei UI", 12, "bold"))

        self._rect = None
        self._sx = self._sy = 0
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.bind("<Escape>", self._cancel)
        self.focus_force()
        self.grab_set()

    def _press(self, event):
        self._sx, self._sy = event.x, event.y
        if self._rect:
            self.canvas.delete(self._rect)
            self._rect = None

    def _drag(self, event):
        if self._rect:
            self.canvas.delete(self._rect)
        self._rect = self.canvas.create_rectangle(
            self._sx, self._sy, event.x, event.y,
            outline=ACCENT, width=2, dash=(6, 4))

    def _release(self, event):
        x1, x2 = sorted((self._sx, event.x))
        y1, y2 = sorted((self._sy, event.y))
        if x2 - x1 < 30 or y2 - y1 < 16:
            if self._rect:
                self.canvas.delete(self._rect)
                self._rect = None
            self.canvas.itemconfigure(self._hint_id, text="区域太小，请重新框选（Esc 取消）")
            return
        region = {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1}
        self.grab_release()
        self.destroy()
        self.on_save(region)

    def _cancel(self, _event=None):
        if self.on_cancel:
            self.on_cancel()
        self.grab_release()
        self.destroy()
