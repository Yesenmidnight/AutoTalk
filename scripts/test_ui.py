"""UI 与交互逻辑测试：验证 AutoTalkApp 在解析、卡片渲染、复制与清空下的稳定性。"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import tkinter as tk
from autotalk.widget import AutoTalkApp


def test_ui():
    print("开始测试 AutoTalkApp UI 逻辑...")
    # 模拟启动应用（关闭 topmost 避免测试弹窗遮挡）
    app = AutoTalkApp()
    app.root.attributes("-topmost", False)

    sample_output = """【NPC 分析】
说话人是云梦泽守崖修士苏浅雪，性格清冷严苛，当前带有审视与戒备，在意玩家是否道心坚定。

【对话意图】
试探玩家的定力与求道动机，给出一道下马威考验。

【推荐回复】
1.【稳妥】晚辈自知仙途险阻，但求道之心如磐石，愿凭实力经受前辈考验。｜预期：好感微增，展现沉稳恪守礼数
2.【进取】若畏惧险阻，晚辈便不会来这问心崖。还请前辈赐教！｜预期：NPC赞许，展现锋芒与锐气
3.【试探】十年苦修固然宝贵，但若能得见前辈仙颜指点，虚掷又何妨？｜预期：触发特殊对话分支，稍显轻浮但易引好感

【小提示】
苏浅雪喜刚毅正直之士，过于奉承可能适得其反。"""

    # 1. 模拟结果返回
    app._set_result(sample_output)
    app.root.update()

    # 检查洞察区内容
    insight_text = app.insight_box.get("1.0", "end")
    assert "苏浅雪" in insight_text, "洞察区未包含 NPC 分析"
    assert "试探玩家的定力" in insight_text, "洞察区未包含对话意图"
    assert "【推荐回复】" not in insight_text, "洞察区不应包含【推荐回复】标题"
    assert "1.【稳妥】" not in insight_text, "洞察区不应混入推荐回复"
    print("1. 局势与 NPC 洞察区独立展示验证通过 ✓")

    # 2. 检查推荐回复卡片
    assert len(app.reply_cards) == 3, f"期望 3 个推荐回复卡片，实际生成 {len(app.reply_cards)}"
    c1 = app.reply_cards[0]
    assert c1.reply_data["tag"] == "稳妥"
    assert "晚辈自知仙途险阻" in c1.reply_data["content"]
    assert "好感微增" in c1.reply_data["expected"]
    print("2. 推荐回复独立卡片生成验证通过 ✓")

    # 3. 模拟复制卡片 1
    c1.do_copy()
    app.root.update()
    clipboard_content = app.root.clipboard_get()
    assert clipboard_content == "晚辈自知仙途险阻，但求道之心如磐石，愿凭实力经受前辈考验。", f"剪贴板内容不符合预期: {clipboard_content}"
    assert "稳妥" in app.status.cget("text"), "状态栏未显示对应标签"
    print("3. 卡片独立复制纯净台词验证通过 ✓")

    # 4. 模拟按数字键 2
    class DummyKeyEvent:
        char = "2"
    app._on_key_press(DummyKeyEvent())
    app.root.update()
    clipboard_content2 = app.root.clipboard_get()
    assert "若畏惧险阻" in clipboard_content2
    assert "进取" in app.status.cget("text")
    print("4. 键盘数字键快捷复制联动验证通过 ✓")

    # 5. 模拟清空
    app._clear_all()
    app.root.update()
    assert len(app.reply_cards) == 0, "清空后卡片列表应为空"
    assert app.insight_box.get("1.0", "end").strip() == "", "清空后洞察区应为空"
    print("5. 清空功能验证通过 ✓")

    app.root.destroy()
    print("全部 UI 自动化验证通过！")


if __name__ == "__main__":
    test_ui()
