"""调用 OpenAI 兼容接口，分析对话并生成推荐回复。"""

import re
import requests

from .config import cfg

SYSTEM_PROMPT = """你是修仙文字冒险游戏《不问凡尘》的资深对话策略师。玩家会把与 NPC 的对话内容发给你
（内容来自屏幕 OCR，可能有错字或断行，请结合语境智能纠正）。

你的任务：把当前对话当作一道"解谜题"，帮玩家选出最能推进 NPC 好感度与关系的回复。

严格按以下格式输出（不要任何开场白或额外说明）：
【NPC 分析】
（说话人是谁、性格特质、当前情绪、TA 在意或需要什么；2~3 句）
【对话意图】
（这句话背后的目的、考验或潜台词；1~2 句）
【推荐回复】
1.【稳妥】<完整回复内容>｜预期：<好感与剧情影响，一句话>
2.【进取】<完整回复内容>｜预期：<好感与剧情影响，一句话>
3.【试探】<完整回复内容>｜预期：<好感与剧情影响，一句话>
【小提示】
（一句补充提醒，可省略）

要求：
- 思考过程务必极速简明，勿冗长推导，直奔主题输出最终正文；
- 回复要贴合修仙世界观与 NPC 的说话风格，符合玩家"修士"身份；
- 三条回复策略差异要明显，标签可用更贴切的自定义词替换"稳妥/进取/试探"；
- 每条推荐回复必须独占一行，且严格按「编号.【策略】回复内容｜预期：影响」格式，不要有多余换行。"""

RE_TAG = re.compile(r"^[【\[]([^】\]]+)[】\]]\s*")
RE_ITEM_SPLIT = re.compile(r"^\s*(?:(\d+)[\.、\s]\s*)?(?:[【\[]([^】\]]+)[】\]]\s*)?(.*?)(?:(?:[|｜]\s*(?:预期[：:])?\s*)(.*))?$")


def parse_analysis(text: str) -> dict:
    """将大模型输出结构化拆解为 insights（NPC分析/意图等）与 replies（推荐回复列表）。

    返回:
        {
            "insights": str,  # 仅包含 NPC 分析、对话意图、小提示等洞察内容
            "replies": [      # 结构化推荐回复列表
                {
                    "index": int,
                    "tag": str,       # 如 "稳妥"、"进取"、"试探"
                    "content": str,   # 纯净台词，可直接粘贴进游戏
                    "expected": str,  # 预期收益/好感影响说明
                    "raw": str,       # 原始单行文本
                }, ...
            ]
        }
    """
    if not text or not text.strip():
        return {"insights": "", "replies": []}

    lines = [line.strip() for line in text.splitlines()]
    
    # 查找各段落分区
    sections = {}
    current_sec = "header"
    sections[current_sec] = []

    for line in lines:
        if not line:
            if sections[current_sec] and sections[current_sec][-1] != "":
                sections[current_sec].append("")
            continue
        # 判断是否是章节标题
        if line.startswith("【") and "】" in line and len(line) <= 20:
            current_sec = line.strip()
            if current_sec not in sections:
                sections[current_sec] = []
            continue
        sections[current_sec].append(line)

    replies = []
    # 寻找推荐回复段
    reply_lines = []
    for sec_name, s_lines in sections.items():
        if "推荐回复" in sec_name or "回复推荐" in sec_name:
            reply_lines = s_lines
            break

    # 若未明确匹配到【推荐回复】段落，扫描所有包含 1.【xxx】或 1. xxx 的行作为兜底
    if not reply_lines:
        for line in lines:
            if re.match(r"^\s*\d+[\.、]", line):
                reply_lines.append(line)

    idx_counter = 1
    for r_line in reply_lines:
        if not r_line.strip():
            continue
        raw = r_line.strip()
        # 移除行首编号，如 "1." 或 "1、"
        m_num = re.match(r"^\s*(\d+)[\.、\s]\s*(.*)$", raw)
        if m_num:
            item_idx = int(m_num.group(1))
            body = m_num.group(2).strip()
        else:
            item_idx = idx_counter
            body = raw

        # 切分预期：找 "｜预期：" 或 "|" 或 "｜"
        tag = ""
        expected = ""
        content = body

        if "｜" in body or "|" in body:
            sep = "｜" if "｜" in body else "|"
            left, right = body.split(sep, 1)
            content = left.strip()
            expected = right.strip()
            if expected.startswith("预期：") or expected.startswith("预期:"):
                expected = expected[3:].strip()

        # 提取标签 【稳妥】
        m_tag = RE_TAG.match(content)
        if m_tag:
            tag = m_tag.group(1).strip()
            content = content[m_tag.end():].strip()
        else:
            # 兼容中括号 [稳妥]
            m_tag2 = re.match(r"^\[(.*?)\]\s*", content)
            if m_tag2:
                tag = m_tag2.group(1).strip()
                content = content[m_tag2.end():].strip()

        # 清洗可能包裹在台词外的全角/半角引号
        content = content.strip("「」\"'“”")

        if content:
            replies.append({
                "index": item_idx,
                "tag": tag or "推荐",
                "content": content,
                "expected": expected,
                "raw": raw,
            })
            idx_counter = item_idx + 1

    # 组装 insights（排除推荐回复段）
    insight_parts = []
    for sec_name, s_lines in sections.items():
        if "推荐回复" in sec_name or "回复推荐" in sec_name or sec_name == "header":
            if sec_name == "header" and s_lines:
                # 过滤掉属于 reply 的行
                valid_header_lines = [l for l in s_lines if not re.match(r"^\s*\d+[\.、]", l)]
                if valid_header_lines:
                    insight_parts.append("\n".join(valid_header_lines))
            continue
        
        sec_content = "\n".join(s_lines).strip()
        if sec_content:
            insight_parts.append(f"{sec_name}\n{sec_content}")

    insights = "\n\n".join(insight_parts).strip()
    if not insights and not replies:
        insights = text.strip()

    return {
        "insights": insights,
        "replies": replies,
    }



def build_messages(history, current):
    parts = []
    if history:
        parts.append(
            "【最近对话快照】（从旧到新，供上下文参考）\n"
            + "\n---\n".join(history)
        )
    parts.append("【当前对话】\n" + (current.strip() or "（空）"))
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def analyze(history, current, timeout=90):
    """调用大模型分析对话，返回回复文本。history 为之前几轮对话快照。"""
    api_key = (cfg.get("api_key") or "").strip()
    if not api_key:
        raise RuntimeError("未配置 API Key，请点击「设置」填写")
    base = (cfg.get("api_base") or "").rstrip("/")
    url = base if base.endswith("/chat/completions") else base + "/chat/completions"
    max_tok = int(cfg.get("max_tokens", 4096))
    if max_tok < 2000:
        max_tok = 4096  # 强制为思维链模型预留至少 4096 tokens

    payload = {
        "model": cfg.get("model") or "deepseek-flash",
        "messages": build_messages(history, current),
        "temperature": float(cfg.get("temperature", 0.7)),
        "max_tokens": max_tok,
    }
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
    except requests.exceptions.SSLError as e:
        raise RuntimeError(
            "连接大模型服务器失败（SSL / 证书握手异常中断）：\n"
            "【快速排查】：\n"
            "1. 若开启了科学上网代理（Clash/V2Ray/VPN）或游戏加速器，请关闭或切换为「规则模式/绕过大陆」；\n"
            "   (api.deepseek.com 位于国内，被海外节点接管易遭防火墙强制断开)\n"
            "2. 检查 Windows 系统设置是否残留了未开启的本地代理端口；\n"
            "3. 若 DeepSeek 官方服务瞬时拥堵，请稍后点击「重新分析」重试。"
        ) from e
    except requests.exceptions.Timeout:
        raise RuntimeError(f"大模型响应超时（超过 {timeout} 秒），请检查网络连接后重试。")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            "网络连接失败，无法访问大模型 API 服务器。\n"
            "请检查网络连接、关闭干扰代理或稍后重试。"
        ) from e

    if resp.status_code != 200:
        msg = "接口返回 %s: %s" % (resp.status_code, resp.text[:300])
        if resp.status_code == 401:
            msg = ("鉴权失败(401)：API Key 无效或已过期，也可能是 Key 与地址类型不匹配。\n"
                   "· 智谱 Coding Plan 订阅 Key → 地址用 https://open.bigmodel.cn/api/coding/paas/v4\n"
                   "· 按量付费 Key → 地址用 https://open.bigmodel.cn/api/paas/v4\n"
                   "若两者都报 401，请到开放平台控制台重新生成 Key 并完整复制。\n"
                   "接口原始返回：" + resp.text[:200])
        elif resp.status_code in (400, 404) and "model" in resp.text.lower():
            msg += "\n（提示：模型名可能不被该地址支持，请检查「设置」里的模型名）"
        elif resp.status_code == 429:
            msg += "\n（提示：请求过于频繁或额度不足）"
        raise RuntimeError(msg)
    data = resp.json()
    try:
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = (msg.get("content") or "").strip()
        reasoning = (msg.get("reasoning_content") or "").strip()
        finish_reason = choice.get("finish_reason", "")

        # 写入简明调用排查日志
        try:
            with open("autotalk_api.log", "a", encoding="utf-8") as f:
                f.write("[API Call] model=%s finish_reason=%s content_len=%d reasoning_len=%d\n" % (
                    payload["model"], finish_reason, len(content), len(reasoning)))
        except Exception:
            pass

        # 若 content 为空，根据情况智能兜底或报错
        if not content:
            if finish_reason == "length":
                raise RuntimeError("大模型思考耗尽了 Token 额度导致正文未能生成（finish_reason: length），请点击「清空」后重新抓取分析")
            if reasoning and ("【推荐回复】" in reasoning or "推荐回复" in reasoning):
                # 兼容某些思考模型将最终回复误放在 reasoning_content 的情况
                content = reasoning
            else:
                raise RuntimeError("大模型返回的正文内容为空，请点击「🔄 重新分析」重试")

        return content
    except Exception as e:
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError("接口响应格式异常: %s" % str(data)[:300])
