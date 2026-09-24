"""AutoTalk 入口：python main.py"""

import ctypes


def _enable_dpi_awareness():
    # 坐标与截图统一使用物理像素，避免高 DPI 缩放导致选区错位
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    _enable_dpi_awareness()
    from autotalk.widget import AutoTalkApp

    AutoTalkApp().run()


if __name__ == "__main__":
    main()
