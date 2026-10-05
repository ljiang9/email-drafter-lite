# email-drafter-lite

零依赖、开箱即用的**场景化邮件草稿生成器**。按求职、请假、催办、感谢、会议邀请等常见场景选择模板，填入变量即可生成中英文邮件正文。可选接入 OpenAI 兼容接口做进一步润色；没有 API key 时自动走模板渲染，核心功能完全可用。

## 功能简介

- 内置 5 类常用场景模板：`job_application`（求职）、`leave`（请假）、`follow_up`（催办）、`thank_you`（感谢）、`meeting_invite`（会议邀请）。
- 每个场景同时提供中文 / 英文两个版本。
- 通过 `key=value` 变量替换生成正文；缺失字段自动保留 `<字段名>` 占位，方便人工补全。
- 可选 LLM 润色（OpenAI 兼容 `chat/completions`，仅用标准库 `urllib`）。

## 快速开始

```bash
# 查看全部场景及所需字段
python3 cli.py --list

# 生成中文请假邮件
python3 cli.py --scene leave --lang zh \
  --var recipient=李经理 --var sender=张三 --var reason="家中有事" \
  --var start_date=10-10 --var end_date=10-12 --var days=3 \
  --var colleague=王五 --var contact=微信

# 生成英文感谢邮件
python3 cli.py --scene thank_you --lang en \
  --var recipient=Alex --var sender=Zhang \
  --var occasion="the interview" --var detail="your feedback on system design"
```

## 无 API key 如何运行

本项目**不依赖任何 API key**。不带 `--llm` 参数时，所有邮件都由本地模板渲染生成，立即可用。
只有当你想要更自然的润色效果时，才需要设置环境变量并加上 `--llm`：

```bash
export OPENAI_API_KEY=sk-xxx
export OPENAI_BASE_URL=https://api.openai.com/v1   # 可选，默认官方地址
export OPENAI_MODEL=gpt-4o-mini                    # 可选
python3 cli.py --scene follow_up --llm --var recipient=王总 --var sender=我 \
  --var topic=合同 --var status=已初稿 --var deadline=周五
```

## 目录说明

```
email-drafter-lite/
├── email_drafter.py   # 模板库 + 渲染逻辑 + 可选 LLM 润色
├── cli.py            # 命令行入口
├── tests/
│   └── test_drafter.py
├── README.md
├── LICENSE
└── .gitignore
```

## 运行测试

```bash
python3 -m unittest discover -s tests
```

## License

MIT License，Copyright (c) 2026 ljiang9。
