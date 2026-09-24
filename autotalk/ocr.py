"""本地 OCR 封装：优先 rapidocr_onnxruntime，兼容新版 rapidocr 包。"""

import numpy as np
from PIL import Image

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _engine = RapidOCR()
        except Exception as e:
            try:
                from rapidocr import RapidOCR
                _engine = RapidOCR()
            except Exception:
                raise e
    return _engine


def _extract_lines(result):
    """兼容不同版本的返回结构，提取纯文本行列表。"""
    if result is None:
        return []
    if isinstance(result, tuple):
        result = result[0]
    txts = getattr(result, "txts", None)
    if txts:
        return [str(t) for t in txts]
    lines = []
    for item in result or []:
        t = getattr(item, "txt", None)
        if t is None and isinstance(item, (list, tuple)) and len(item) >= 2:
            t = item[1]
        if t:
            lines.append(str(t))
    return lines


def recognize(img, min_width_for_upscale=600):
    """对 PIL.Image 做 OCR，返回按行拼接的文本。小区域自动放大以提升精度。"""
    engine = _get_engine()
    if img.width < min_width_for_upscale:
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    result = engine(np.asarray(img.convert("RGB")))
    return "\n".join(_extract_lines(result))
