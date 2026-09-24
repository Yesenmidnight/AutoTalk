"""历史记录管理：按每次打开软件的时间戳生成 Markdown 归档文件。"""

import os
import sys
import time
from datetime import datetime

from .config import cfg

if getattr(sys, "frozen", False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HISTORY_DIR = os.path.join(ROOT_DIR, "history")


class HistoryRecorder:
    def __init__(self):
        self.folder = HISTORY_DIR
        self.turn_count = 0
        self.start_time = datetime.now()
        self.file_path = None
        self._init_session_file()

    def _init_session_file(self):
        try:
            os.makedirs(self.folder, exist_ok=True)
            stamp = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
            self.file_path = os.path.join(self.folder, f"history_{stamp}.md")

            win_spec = cfg.get("window")
            win_title = win_spec.get("title", "未绑定") if win_spec else "未绑定"
            model_name = cfg.get("model", "默认")

            header = [
                "# 《不问凡尘》AutoTalk 对话历史记录",
                f"- **会话启动时间**：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **使用大模型**：`{model_name}`",
                f"- **目标游戏窗口**：`{win_title}`",
                "",
                "---",
                "",
            ]
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(header))
        except Exception as e:
            print(f"[HistoryRecorder] 初始化历史文件失败: {e}")

    def record_turn(self, ocr_text, insights, replies):
        """记录单轮对话分析。"""
        if not self.file_path:
            return
        try:
            self.turn_count += 1
            now_str = datetime.now().strftime("%H:%M:%S")

            lines = [
                f"## 轮次 {self.turn_count} · {now_str}",
                "",
                "### 📥 游戏对话原文",
            ]
            if ocr_text and ocr_text.strip():
                for o_line in ocr_text.strip().splitlines():
                    lines.append(f"> {o_line}")
            else:
                lines.append("> （空）")
            lines.append("")

            lines.append("### 💡 局势与 NPC 洞察")
            if insights and insights.strip():
                lines.append(insights.strip())
            else:
                lines.append("（无洞察分析）")
            lines.append("")

            lines.append("### 💬 推荐回复")
            if replies:
                for idx, r in enumerate(replies, 1):
                    tag = r.get("tag", "推荐")
                    content = r.get("content", "")
                    expected = r.get("expected", "")
                    lines.append(f"{idx}. **【{tag}】** {content}")
                    if expected:
                        lines.append(f"   - *预期收益*：{expected}")
            else:
                lines.append("（未提取出推荐回复）")
            lines.append("")
            lines.append("---")
            lines.append("")

            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception as e:
            print(f"[HistoryRecorder] 写入历史记录失败: {e}")

    def record_copy(self, reply_data):
        """记录玩家在当前轮次中复制的具体台词。"""
        if not self.file_path:
            return
        try:
            now_str = datetime.now().strftime("%H:%M:%S")
            tag = reply_data.get("tag", "推荐")
            content = reply_data.get("content", "")

            copy_note = f"> 📋 **玩家复制了【{tag}】**：{content} （复制时间：{now_str}）\n\n"

            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(copy_note)
        except Exception as e:
            print(f"[HistoryRecorder] 记录复制动作失败: {e}")

    def open_folder(self):
        """在系统资源管理器中打开历史记录文件夹。"""
        try:
            os.makedirs(self.folder, exist_ok=True)
            if hasattr(os, "startfile"):
                os.startfile(self.folder)
            else:
                import subprocess
                subprocess.Popen(["explorer", self.folder])
        except Exception as e:
            print(f"[HistoryRecorder] 打开文件夹失败: {e}")
