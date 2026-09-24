"""Windows 窗口枚举与定位（ctypes 标准库实现，无第三方依赖）。

坐标均为物理像素（进程在 main.py 中已开启 DPI awareness），
与 mss 截屏坐标系一致，多显示器（含负坐标副屏）天然支持。
"""

import ctypes
import os
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
dwmapi = ctypes.windll.dwmapi

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
DWMWA_CLOAKED = 14
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def _get_text(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def _get_exe(hwnd):
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value)
        return ""
    finally:
        kernel32.CloseHandle(handle)


def _is_cloaked(hwnd):
    """过滤不可见的 UWP/虚拟桌面窗口。"""
    val = wintypes.DWORD(0)
    dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(val), ctypes.sizeof(val))
    return val.value != 0


def _client_box(hwnd):
    """客户区原点的屏幕绝对坐标 + 客户区尺寸。"""
    crect = RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(crect)):
        return None
    pt = POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(pt)):
        return None
    return {"x": pt.x, "y": pt.y,
            "w": crect.right - crect.left, "h": crect.bottom - crect.top}


def list_windows():
    """列出所有可见、有标题、有实际尺寸的应用窗口，按面积从大到小排序。"""
    results = []

    def cb(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd) or _is_cloaked(hwnd):
            return True
        title = _get_text(hwnd)
        if not title.strip():
            return True
        if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
            return True
        box = _client_box(hwnd)
        if not box or box["w"] < 150 or box["h"] < 100:
            return True
        results.append({"hwnd": hwnd, "title": title, "exe": _get_exe(hwnd), "box": box})
        return True

    proc = EnumWindowsProc(cb)
    user32.EnumWindows(proc, 0)
    results.sort(key=lambda w: -(w["box"]["w"] * w["box"]["h"]))
    return results


def find_window(spec):
    """按 {title, exe} 找回窗口句柄，精确标题优先。找不到返回 None。"""
    if not spec:
        return None
    title = (spec.get("title") or "").strip()
    exe = (spec.get("exe") or "").strip().lower()
    best, best_score = None, 0
    for w in list_windows():
        score = 0
        if title:
            if w["title"] == title:
                score = 4
            elif title in w["title"] or w["title"] in title:
                score = 2
        if exe and w["exe"].lower() == exe:
            score += 1
        if score > best_score:
            best, best_score = w, score
    return best["hwnd"] if best else None


def get_client_box(spec):
    """解析已保存的游戏窗口，返回其客户区的屏幕绝对坐标与尺寸。"""
    hwnd = find_window(spec)
    if hwnd is None:
        raise RuntimeError("找不到已设置的游戏窗口（可能已关闭或改名），请重新「选游戏窗口」")
    if user32.IsIconic(hwnd):
        raise RuntimeError("游戏窗口当前已最小化，请先恢复它再操作")
    box = _client_box(hwnd)
    if not box or box["w"] < 50 or box["h"] < 50:
        raise RuntimeError("无法获取游戏窗口尺寸")
    return box
