"""单元测试：验证大模型输出的结构化拆分与鲁棒性。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from autotalk.analyzer import parse_analysis


def test_standard():
    sample = """【NPC 分析】
说话人是云梦泽守崖修士苏浅雪，性格清冷严苛，当前带有审视与戒备，在意玩家是否道心坚定。

【对话意图】
试探玩家的定力与求道动机，给出一道下马威考验。

【推荐回复】
1.【稳妥】晚辈自知仙途险阻，但求道之心如磐石，愿凭实力经受前辈考验。｜预期：好感微增，展现沉稳恪守礼数
2.【进取】若畏惧险阻，晚辈便不会来这问心崖。还请前辈赐教！｜预期：NPC赞许，展现锋芒与锐气
3.【试探】十年苦修固然宝贵，但若能得见前辈仙颜指点，虚掷又何妨？｜预期：触发特殊对话分支，稍显轻浮但易引好感

【小提示】
苏浅雪喜刚毅正直之士，过于奉承可能适得其反。"""

    res = parse_analysis(sample)
    assert len(res["replies"]) == 3, f"期望 3 条回复，实际 {len(res['replies'])}"
    r1 = res["replies"][0]
    assert r1["index"] == 1
    assert r1["tag"] == "稳妥"
    assert "晚辈自知仙途险阻" in r1["content"]
    assert "好感微增" in r1["expected"]

    assert "苏浅雪" in res["insights"]
    assert "试探玩家的定力" in res["insights"]
    assert "过于奉承" in res["insights"]
    assert "【推荐回复】" not in res["insights"]
    print("test_standard 通过 ✓")


def test_variation_format():
    # 测试不同的格式变体：缺少小提示，半角管道符，无括号等
    sample = """【NPC 分析】
神秘老者，高深莫测。

【对话意图】
询问来意。

【推荐回复】
1. [恭敬] 弟子路过此地，特来拜会前辈。 | 预期: 礼貌通过
2. 【直接】敢问前辈此处可是机缘所在？ | 问出真相
3. 晚辈并无恶意，只是迷路至此。
"""
    res = parse_analysis(sample)
    assert len(res["replies"]) == 3
    assert res["replies"][0]["tag"] == "恭敬"
    assert res["replies"][0]["expected"] == "礼貌通过"
    assert res["replies"][1]["tag"] == "直接"
    assert res["replies"][1]["expected"] == "问出真相"
    assert res["replies"][2]["tag"] == "推荐"
    assert res["replies"][2]["content"] == "晚辈并无恶意，只是迷路至此。"
    print("test_variation_format 通过 ✓")


def test_fallback_no_sections():
    sample = """苏浅雪似乎在观察你。
1. 我是来拜师的。
2. 我只是路过。"""
    res = parse_analysis(sample)
    assert len(res["replies"]) == 2
    assert res["replies"][0]["content"] == "我是来拜师的。"
    print("test_fallback_no_sections 通过 ✓")


if __name__ == "__main__":
    test_standard()
    test_variation_format()
    test_fallback_no_sections()
    print("全部解析测试通过！")
