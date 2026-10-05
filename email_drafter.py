"""email-drafter-lite：场景化邮件草稿生成器。

按场景（求职 / 请假 / 催办 / 感谢 / 会议邀请 / 道歉等）选用模板，
填入变量生成中英文邮件正文。无 LLM key 时走模板渲染，核心功能完整；
有 OPENAI_API_KEY 时可选调用 LLM 润色。
"""

from __future__ import annotations

import json
import os
import urllib.request

# ---------------------------------------------------------------------------
# 模板库：每个场景提供中文 / 英文两个版本，使用 {占位符} 做变量替换。
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, dict[str, str]] = {
    "job_application": {
        "zh": (
            "尊敬的 {recipient}：\n\n"
            "您好！我是 {sender}，近期了解到 {company} 正在招聘 {position} 岗位，"
            "特此写信表达我的应聘意向。\n\n"
            "我拥有 {years} 年相关经验，曾在 {prev_company} 负责 {highlight}，"
            "与贵岗位的要求高度契合。随信附上我的简历，期待能有机会进一步沟通。\n\n"
            "感谢您拨冗阅读，静候回音。\n\n"
            "此致\n敬礼\n{sender}"
        ),
        "en": (
            "Dear {recipient},\n\n"
            "My name is {sender}, and I am writing to apply for the {position} "
            "opening at {company}.\n\n"
            "I have {years} years of relevant experience, most recently at "
            "{prev_company}, where I worked on {highlight}. I believe my "
            "background is a strong match for this role. My resume is attached "
            "for your consideration.\n\n"
            "Thank you for your time. I look forward to hearing from you.\n\n"
            "Best regards,\n{sender}"
        ),
    },
    "leave": {
        "zh": (
            "{recipient} 您好：\n\n"
            "因 {reason}，我计划于 {start_date} 至 {end_date} 请假，共计 {days} 天。\n\n"
            "请假期间，我已将手头工作交接给 {colleague}，紧急事宜可通过 {contact} 联系到我。"
            "回来后我会及时补进进度。\n\n"
            "恳请批准，谢谢！\n\n{sender}"
        ),
        "en": (
            "Hi {recipient},\n\n"
            "I am writing to request leave from {start_date} to {end_date} "
            "({days} days) due to {reason}.\n\n"
            "During my absence, I have handed over my ongoing work to "
            "{colleague}; for urgent matters, I can be reached at {contact}. "
            "I will catch up on progress upon my return.\n\n"
            "Thank you for your consideration.\n\n{sender}"
        ),
    },
    "follow_up": {
        "zh": (
            "{recipient} 您好：\n\n"
            "距离我们上次沟通已过去一段时间，想就「{topic}」这件事跟您同步一下进展。\n\n"
            "目前的状态是 {status}，我希望能在 {deadline} 前得到您的反馈，"
            "以便我们顺利推进后续安排。如果时间上有困难，也请告知，我来调整计划。\n\n"
            "辛苦您了，谢谢！\n\n{sender}"
        ),
        "en": (
            "Hi {recipient},\n\n"
            "It has been a little while since we last spoke, so I wanted to "
            "follow up on \"{topic}\".\n\n"
            "The current status is: {status}. I would appreciate your feedback "
            "by {deadline} so we can move things forward. If that timeline "
            "does not work, just let me know and I will adjust.\n\n"
            "Thanks very much!\n\n{sender}"
        ),
    },
    "thank_you": {
        "zh": (
            "{recipient} 您好：\n\n"
            "非常感谢您在 {occasion} 中给予我的帮助与支持。您在 {detail} 上的建议，"
            "让我受益匪浅。\n\n"
            "希望以后也有机会能回报这份善意。再次感谢，祝一切顺利！\n\n{sender}"
        ),
        "en": (
            "Dear {recipient},\n\n"
            "Thank you so much for your help and support during {occasion}. "
            "Your advice on {detail} was truly valuable to me.\n\n"
            "I hope I can return the kindness someday. Thanks again, and all the best!\n\n{sender}"
        ),
    },
    "meeting_invite": {
        "zh": (
            "{recipient} 您好：\n\n"
            "想邀请您参加一场会议，时间定为 {time}，形式为 {format}。\n\n"
            "本次会议主要讨论 {agenda}，预计时长约 {duration}。相关材料见附件 / 链接，"
            "如时间不便，请直接回复告知合适的时段。\n\n"
            "期待与您见面！\n\n{sender}"
        ),
        "en": (
            "Hi {recipient},\n\n"
            "I would like to invite you to a meeting scheduled for {time}, "
            "held via {format}.\n\n"
            "We will mainly discuss {agenda}; it should last about {duration}. "
            "Materials are attached. If the time does not work, just reply with "
            "an alternative.\n\n"
            "Looking forward to meeting you!\n\n{sender}"
        ),
    },
}

SCENARIUS = tuple(TEMPLATES.keys())


def list_scenarios() -> list[str]:
    """返回全部可用场景名。"""
    return list(TEMPLATES.keys())


def required_fields(scenario: str, lang: str = "zh") -> list[str]:
    """返回某场景模板所需的占位符字段名列表。"""
    if scenario not in TEMPLATES:
        raise KeyError(f"未知场景：{scenario}")
    tpl = TEMPLATES[scenario][lang]
    fields: list[str] = []
    for token in _PLACEHOLDER.findall(tpl):
        if token not in fields:
            fields.append(token)
    return fields


import re as _re
_PLACEHOLDER = _re.compile(r"\{(\w+)\}")


def render(scenario: str, values: dict[str, str], lang: str = "zh") -> str:
    """根据场景与变量渲染邮件正文。

    缺失的占位符会被替换成 <字段名> 占位标记，便于人工补全，不抛异常。
    """
    if scenario not in TEMPLATES:
        raise KeyError(f"未知场景：{scenario}，可用：{list_scenarios()}")
    if lang not in ("zh", "en"):
        raise ValueError("lang 仅支持 zh / en")
    tpl = TEMPLATES[scenario][lang]

    def _sub(match: _re.Match) -> str:
        key = match.group(1)
        return str(values.get(key, f"<{key}>"))

    return _PLACEHOLDER.sub(_sub, tpl)


# ---------------------------------------------------------------------------
# 可选 LLM 润色（OpenAI 兼容接口，urllib 实现）
# ---------------------------------------------------------------------------

def polish_llm(draft: str, api_key: str | None = None,
               base_url: str | None = None, model: str | None = None) -> str:
    """调用 LLM 把草稿润色得更自然得体。无 key 抛 RuntimeError。"""
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    base_url = (base_url or os.environ.get("OPENAI_BASE_URL")
                or "https://api.openai.com/v1").rstrip("/")
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        raise RuntimeError("未设置 OPENAI_API_KEY，无法使用 LLM 润色")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是专业的商务邮件写作助手，输出润色后的邮件正文，不要解释。"},
            {"role": "user", "content": f"请润色下面这封邮件，使其更自然、得体、简洁：\n\n{draft}"},
        ],
        "temperature": 0.5,
    }
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def draft(scenario: str, values: dict[str, str], lang: str = "zh",
          use_llm: bool = False) -> str:
    """统一入口：先模板渲染；若启用 LLM 且有 key，则再润色。"""
    body = render(scenario, values, lang)
    if use_llm and os.environ.get("OPENAI_API_KEY"):
        try:
            return polish_llm(body)
        except Exception as exc:  # 网络失败时降级为模板结果
            print(f"[warn] LLM 润色失败，使用模板草稿：{exc}")
    return body
