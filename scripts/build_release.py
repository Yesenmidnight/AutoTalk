"""AutoTalk 绿色便携版一键打包脚本（基于 PyInstaller）"""

import os
import shutil
import subprocess
import sys
import zipfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")

EXCLUDE_MODULES = [
    "torch",
    "torchvision",
    "torchaudio",
    "scipy",
    "pandas",
    "matplotlib",
    "seaborn",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "IPython",
    "jupyter",
    "notebook",
    "playwright",
    "pypandoc",
    "numba",
    "llvmlite",
    "sklearn",
    "scikit-learn",
    "sympy",
    "pytest",
]


def build():
    os.chdir(ROOT_DIR)

    # 清理旧目录
    for p in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "AutoTalk",
        "--collect-data",
        "rapidocr_onnxruntime",
        "main.py",
    ]
    for mod in EXCLUDE_MODULES:
        cmd.extend(["--exclude-module", mod])

    print("=" * 60)
    print("开始打包 AutoTalk 绿色便携版...")
    print("=" * 60)
    subprocess.check_call(cmd)

    app_dir = os.path.join(DIST_DIR, "AutoTalk")

    # 拷贝模板配置
    example_cfg = os.path.join(ROOT_DIR, "config.example.json")
    if os.path.exists(example_cfg):
        shutil.copy2(example_cfg, app_dir)

    # 拷贝 README
    readme = os.path.join(ROOT_DIR, "README.md")
    if os.path.exists(readme):
        shutil.copy2(readme, app_dir)

    # 剔除未使用的 OpenCV 视频编解码大体积 DLL (节约近 30MB)
    cv2_dir = os.path.join(app_dir, "_internal", "cv2")
    if os.path.exists(cv2_dir):
        for f in os.listdir(cv2_dir):
            if f.startswith("opencv_videoio_ffmpeg") and f.endswith(".dll"):
                try:
                    os.remove(os.path.join(cv2_dir, f))
                except Exception:
                    pass

    # 压缩为 Zip 方便用户一键下载 (输出标准 ASCII 命名以兼容海外/CI 服务器)
    zip_path_en = os.path.join(DIST_DIR, "AutoTalk-v1.0-Windows-x64-Portable.zip")
    zip_path_cn = os.path.join(DIST_DIR, "AutoTalk_v1.0_Windows_x64_便携绿色版.zip")
    print("\nCompressing portable package...")
    with zipfile.ZipFile(zip_path_en, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(app_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, DIST_DIR)
                zf.write(full_path, rel_path)
    shutil.copy2(zip_path_en, zip_path_cn)

    size_mb = os.path.getsize(zip_path_en) / (1024 * 1024)
    print("=" * 60)
    print(f"Build complete! Package: {zip_path_en}")
    print(f"Package size: {size_mb:.2f} MB")
    print("Double click AutoTalk.exe to run directly without installing Python!")
    print("=" * 60)


if __name__ == "__main__":
    build()
