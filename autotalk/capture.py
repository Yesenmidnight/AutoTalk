"""屏幕区域截图（mss，纯截屏方案，不碰游戏进程）。"""

import os
import time

import mss
from PIL import Image


def grab_region(region):
    """截取屏幕绝对坐标区域，region: {"x","y","w","h"}，返回 PIL.Image (RGB)。

    多显示器下 x/y 可为负数（mss 使用虚拟屏幕坐标系）。
    """
    if not region or not region.get("w") or not region.get("h"):
        raise RuntimeError("尚未设置对话区域，请先点击「框选对话区」")
    box = {
        "left": int(region["x"]),
        "top": int(region["y"]),
        "width": int(region["w"]),
        "height": int(region["h"]),
    }
    with mss.mss() as sct:
        shot = sct.grab(box)
    return Image.frombytes("RGB", shot.size, shot.rgb)


def save_capture(img, folder="captures"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, time.strftime("cap_%Y%m%d_%H%M%S.png"))
    img.save(path)
    return path
