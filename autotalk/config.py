"""配置加载与保存（config.json）。"""

import json
import os
import sys

if getattr(sys, "frozen", False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
CONFIG_EXAMPLE_PATH = os.path.join(ROOT_DIR, "config.example.json")

DEFAULTS = {
    "api_base": "https://open.bigmodel.cn/api/coding/paas/v4",
    "api_key": "",
    "model": "glm-5.3-flash",
    "hotkey": "ctrl+alt+t",
    "window": None,  # {"title": str, "exe": str} 游戏窗口标识
    "region": None,  # {"x": int, "y": int, "w": int, "h": int} 相对游戏窗口客户区
    "watch_interval_sec": 3.0,
    "history_limit": 6,
    "save_captures": False,
    "temperature": 0.7,
    "max_tokens": 4096,
}


class Config:
    def __init__(self):
        self.data = dict(DEFAULTS)
        self.load()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def load(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except Exception as e:
                print("配置读取失败，使用默认配置:", e)
        elif os.path.exists(CONFIG_EXAMPLE_PATH):
            try:
                with open(CONFIG_EXAMPLE_PATH, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except Exception as e:
                pass

    def save(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)


cfg = Config()
