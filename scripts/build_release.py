"""AutoTalk 绿色便携版一键打包脚本（基于 PyInstaller）"""

import os
import shutil
import subprocess
import sys
import zipfile

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
    "cv2",
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

    # 压缩为 Zip 方便用户一键下载
    zip_path = os.path.join(DIST_DIR, "AutoTalk_v1.0_Windows_x64_便携绿色版.zip")
    print("\n正在压缩绿色整合包...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(app_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, DIST_DIR)
                zf.write(full_path, rel_path)

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print("=" * 60)
    print(f"打包成功！整合包路径: {zip_path}")
    print(f"压缩包大小: {size_mb:.2f} MB")
    print("解压后双击 AutoTalk.exe 即可直接运行，无需安装 Python！")
    print("=" * 60)


if __name__ == "__main__":
    build()
