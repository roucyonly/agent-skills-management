# Skills Management System

Skill 生命周期管理工具。自动追踪 skill 调用，提供使用统计、维护建议和周期报告。

## 管理命令

| 命令 | 用途 |
|------|------|
| `/scan` | 扫描目录，发现并注册 skill |
| `/stats` | 查看 skill 使用统计和趋势 |
| `/maintain` | 维护：废弃建议、合并建议、日志压缩 |
| `/report` | 生成周期性使用报告 |

## 架构

- **hooks/**: 两个 Python hook 脚本，通过 PreToolUse/PostToolUse 自动记录 Skill 工具调用到 `data/usage.jsonl`
- **skills/**: 4 个 SKILL.md 定义管理命令（Claude 执行分析，不是 Python 代码）
- **data/registry.json**: skill 注册表
- **data/usage.jsonl**: 追加型事件日志

## 数据路径

所有数据文件在 `~/.claude/skills-management/data/` 下：
- `registry.json` — skill 注册表（由 `/scan` 维护）
- `usage.jsonl` — 事件日志（由 hooks 自动追加）
- `reports/` — 周期报告（由 `/report` 生成）
