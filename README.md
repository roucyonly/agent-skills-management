# Skills Management System

Claude Code 的 Skill 生命周期管理工具。自动追踪调用，提供统计、维护建议和周期报告。

## 架构

核心思路：**Python 只做轻量记录（~50 行 hook 脚本），所有分析由 Claude 通过 SKILL.md 指令完成。**

```
~/.claude/skills-management/
├── hooks/
│   ├── pre-skill.py       # PreToolUse hook → 记录 skill 调用开始
│   └── post-skill.py      # PostToolUse hook → 记录 skill 调用结束
├── .claude/skills/
│   ├── scan/SKILL.md      # /scan - 扫描并注册 skill
│   ├── stats/SKILL.md     # /stats - 使用统计
│   ├── maintain/SKILL.md  # /maintain - 维护、合并、废弃
│   └── report/SKILL.md    # /report - 周期报告
├── data/
│   ├── registry.json      # skill 注册表
│   └── usage.jsonl        # 追加型事件日志（hooks 自动写入）
├── CLAUDE.md
└── README.md
```

## 安装

1. Hooks 已配置在 `~/.claude/settings.json` 中，无需额外操作
2. 重启 Claude Code 使 hooks 生效

## 使用

在 skills-management 项目目录下，使用以下斜杠命令：

| 命令 | 用途 |
|------|------|
| `/scan` | 扫描目录，发现并注册 skill |
| `/stats` | 查看 skill 使用统计和趋势 |
| `/maintain` | 废弃建议、合并建议、日志压缩 |
| `/report` | 生成周期性使用报告 |

## 数据格式

### usage.jsonl（追加型事件日志）

每次 Skill 工具被调用时，hooks 自动追加记录：

```jsonl
{"event":"skill_start","ts":"2026-05-17T14:23:01","session_id":"abc","skill":"web-automation","source":"tool"}
{"event":"skill_end","ts":"2026-05-17T14:23:45","session_id":"abc","skill":"web-automation","success":true}
```

### registry.json（skill 注册表）

由 `/scan` 命令维护：

```json
{
  "version": 1,
  "last_updated": "2026-05-17T14:00:00",
  "skills": {
    "skill-name": {
      "name": "skill-name",
      "description": "...",
      "path": "/path/to/SKILL.md",
      "source": "local",
      "tags": ["tag1"],
      "status": "active",
      "registered_at": "2026-05-04T21:55:08"
    }
  }
}
```

## 与旧版的区别

| | 旧版 | 新版 |
|--|------|------|
| 代码量 | ~5100 行 Python | ~50 行 Python + ~250 行 SKILL.md |
| 分析方式 | Python 关键词匹配 | Claude 语义理解 |
| 数据存储 | YAML 读-改-写 | JSONL 追加写入 |
| 依赖 | pyyaml, click, rich, watchdog | 无（纯标准库） |
| Hook 解析 | 错误（从 data.tool_name 读取） | 正确（从顶层 tool_name 读取） |
