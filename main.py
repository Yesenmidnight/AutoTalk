"""AutoTalk 入口：python main.py"""

import ctypes
import os
import sys


def check_python_version():
    """检查 Python 版本，拦截不支持的 Python 3.13+"""
    if getattr(sys, "frozen", False):
        return
    if sys.version_info >= (3, 13):
        print("=" * 68)
        print(f"[AutoTalk 环境错误] 当前 Python 版本为 {sys.version.split()[0]} (不支持)")
        print("原因：核心离线 OCR 库 (rapidocr-onnxruntime) 官方限定要求: Python < 3.13")
        print("在 Python 3.13 及更高版本中无法安装该库。")
        print("-" * 68)
        print("【彻底解决办法】请安装官方推荐的 64 位 Python 3.12（官方安装包直链）：")
        print("https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe")
        print("（安装时请务必勾选底部的 'Add python.exe to PATH'）")
        print("安装完成后，直接双击运行 [启动AutoTalk.bat] 即可自动识别启动！")
        print("=" * 68)
        try:
            input("\n按回车键退出...")
        except Exception:
            pass
        sys.exit(1)


def ensure_dependencies():
    """检查必要依赖，若缺失则自动通过国内镜像安装。"""
    if getattr(sys, "frozen", False):
        return
    packages = [
        ("requests", "requests>=2.28"),
        ("PIL", "Pillow>=9.5"),
        ("mss", "mss>=9.0"),
        ("keyboard", "keyboard>=0.13.5"),
        ("numpy", "numpy>=1.24"),
        ("rapidocr_onnxruntime", "rapidocr-onnxruntime>=1.3.7"),
    ]

    missing = []
    for mod_name, pkg_spec in packages:
        try:
            __import__(mod_name)
        except ImportError:
            missing.append(pkg_spec)

    if not missing:
        return

    print("=" * 60)
    print("[AutoTalk] 检测到当前 Python 环境缺少运行依赖：")
    for pkg in missing:
        print(f"  - {pkg}")
    print("正在通过国内清华镜像源自动安装，请稍候...")
    print("=" * 60)

    import subprocess

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-i",
        "https://pypi.tuna.tsinghua.edu.cn/simple",
    ] + missing

    try:
        ret = subprocess.call(cmd)
        if ret != 0:
            print("\n[AutoTalk] 清华源安装遇到波动，正在尝试阿里云镜像源重试...")
            cmd_ali = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-i",
                "https://mirrors.aliyun.com/pypi/simple/",
            ] + missing
            ret = subprocess.call(cmd_ali)
            if ret != 0:
                raise RuntimeError(f"pip install exited with code {ret}")
        print("\n[AutoTalk] 依赖安装完成！正在启动程序...\n")
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"[AutoTalk 错误] 依赖自动安装未成功: {e}")
        print("请尝试手动在当前终端执行以下命令进行安装：")
        print(
            f"  {sys.executable} -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple"
        )
        print("\n常见原因排查：")
        print("1. 必须使用 64 位 Python（推荐 3.10 ~ 3.12 版本，32位不支持 OCR）")
        print("2. 若提示权限不足，请在命令末尾添加 --user 选项")
        print("3. 若缺失运行库，请安装微软 Visual C++ 2015-2022 x64 运行库")
        print("=" * 60 + "\n")
        try:
            input("按回车键退出...")
        except Exception:
            pass
        sys.exit(1)


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
    if not getattr(sys, "frozen", False):
        check_python_version()
        ensure_dependencies()

    from autotalk.widget import AutoTalkApp

    AutoTalkApp().run()


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    main()
