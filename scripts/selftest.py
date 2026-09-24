"""离线自检：生成一张模拟游戏对话图片，验证 OCR 链路与配置读写。

用法: py -3 scripts/selftest.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont

from autotalk import ocr
from autotalk.config import Config

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]


def make_sample(path):
    img = Image.new("RGB", (840, 280), (16, 18, 26))
    draw = ImageDraw.Draw(img)
    font = None
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            font = ImageFont.truetype(p, 26)
            break
    if font is None:
        raise RuntimeError("找不到中文字体，无法生成测试图")
    lines = [
        "【云梦泽 · 苏浅雪】",
        "「你既有胆量踏入问心崖，可知此地一步踏错，",
        "便是十年苦修付诸东流？」",
        "（她袖口灵光微动，正静静审视你的来意）",
    ]
    y = 30
    for line in lines:
        draw.text((32, y), line, font=font, fill=(235, 238, 245))
        y += 56
    img.save(path)
    return img


def main():
    print("[1/3] 配置读写检查...")
    conf = Config()
    assert conf.get("api_base"), "配置 api_base 缺失"
    print("      api_base =", conf.get("api_base"))

    print("[2/3] 生成模拟对话图片...")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_dialogue.png")
    img = make_sample(path)
    print("      已生成:", path)

    print("[3/3] OCR 识别（首次运行需加载模型，稍慢）...")
    text = ocr.recognize(img)
    print("---- OCR 结果 ----")
    print(text)
    print("------------------")

    ok = ("问心崖" in text.replace(" ", "")) or len(text.strip()) >= 15
    print("自检结果:", "通过 ✓" if ok else "未通过（请检查依赖安装）")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
