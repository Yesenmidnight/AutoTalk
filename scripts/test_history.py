"""单元测试：验证按时间戳分文件归档的 HistoryRecorder 模块。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from autotalk.history import HistoryRecorder


def test_history_recorder():
    recorder = HistoryRecorder()
    assert os.path.isdir(recorder.folder), "history 文件夹未创建"
    assert os.path.isfile(recorder.file_path), "时间戳命名的 md 文件未生成"

    fname = os.path.basename(recorder.file_path)
    print("生成的时间戳文件:", fname)
    assert fname.startswith("history_"), "文件名应以 history_ 开头"
    assert fname.endswith(".md"), "文件名应以 .md 结尾"

    # 1. 模拟记录第 1 轮
    ocr1 = "郁承锋\n独自练时，我还能够一处处做稳。旁边一有人停下来看，我便总想快些证明自己，脚下反而连着乱。"
    insights1 = "【NPC 分析】\n郁承锋是心气极高的年轻修士，表面自嘲实则极在意旁人目光。\n\n【对话意图】\n试探你是否会看轻他。"
    replies1 = [
        {
            "index": 1,
            "tag": "稳妥",
            "content": "能在人前乱，说明你心里那口气还没散。肯说出来，比死撑面子的人强出十倍。",
            "expected": "好感稳步上升，视你为可吐真言之人",
        },
        {
            "index": 2,
            "tag": "进取",
            "content": "巧了，我这几日也在练桩。明日辰时你我互相盯着练，谁先乱谁请灵茶，如何？",
            "expected": "好感明显提升，解锁同修支线",
        },
    ]

    recorder.record_turn(ocr1, insights1, replies1)

    # 2. 模拟玩家复制进取选项
    recorder.record_copy(replies1[1])

    # 3. 模拟记录第 2 轮
    ocr2 = "郁承锋\n好！一言为定。明日辰时，谁若不来谁是缩头乌龟！"
    insights2 = "【NPC 分析】\n郁承锋面露振奋，少年心性展露无遗。"
    replies2 = [
        {
            "index": 1,
            "tag": "稳妥",
            "content": "一言为定，我必准时到。",
            "expected": "契合守信之风",
        }
    ]
    recorder.record_turn(ocr2, insights2, replies2)

    # 4. 读取文件内容进行校验
    with open(recorder.file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "《不问凡尘》AutoTalk 对话历史记录" in content
    assert "轮次 1" in content
    assert "郁承锋" in content
    assert "玩家复制了【进取】" in content
    assert "轮次 2" in content
    assert "一言为定" in content

    print("HistoryRecorder 功能验证通过 ✓")


if __name__ == "__main__":
    test_history_recorder()
