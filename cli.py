"""email-drafter-lite 命令行入口。

用法示例：
    python3 cli.py --list
    python3 cli.py --scene job_application --lang zh \
        --var recipient=王经理 --var sender=张三 --var company=某科技 \
        --var position=后端工程师 --var years=3 --var prev_company=甲公司 \
        --var highlight="高并发订单系统设计"
    python3 cli.py --scene thank_you --lang en --var recipient=Alex \
        --var sender=Zhang --var occasion="the interview" \
        --var detail="your feedback on system design"
"""

from __future__ import annotations

import argparse
import sys

from email_drafter import draft, list_scenarios, required_fields


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="email-drafter-lite",
        description="零依赖的场景化邮件草稿生成器（中英文，可选 LLM 润色）",
    )
    p.add_argument("--list", action="store_true", help="列出全部可用场景")
    p.add_argument("--scene", help="场景名，如 job_application / leave / follow_up / thank_you")
    p.add_argument("--lang", choices=["zh", "en"], default="zh", help="语言，默认 zh")
    p.add_argument("--var", action="append", default=[],
                   help="以 key=value 形式提供模板变量，可重复传入")
    p.add_argument("--llm", action="store_true", help="启用 LLM 润色（需 OPENAI_API_KEY）")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        print("可用场景：")
        for s in list_scenarios():
            print(f"  - {s}  需要字段：{required_fields(s, args.lang)}")
        return 0

    if not args.scene:
        print("错误：请用 --scene 指定场景，或用 --list 查看", file=sys.stderr)
        return 2

    values: dict[str, str] = {}
    for item in args.var:
        if "=" not in item:
            print(f"错误：--var 需要 key=value，收到：{item}", file=sys.stderr)
            return 2
        k, v = item.split("=", 1)
        values[k.strip()] = v.strip()

    body = draft(args.scene, values, lang=args.lang, use_llm=args.llm)
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
