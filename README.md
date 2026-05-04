# Skills Management System

完整的 Claude Code 技能管理系统，支持自动发现、使用统计、清理维护等功能。

## 功能特性

✅ **自动发现** - 自动发现新建的技能，无论以何种方式安装
✅ **使用统计** - 追踪技能使用情况和成功率
✅ **智能管理** - 自动注册、更新、去重
✅ **冷热数据分离** - 只加载最近2个月的数据，保持高性能
✅ **完整功能** - 搜索、过滤、统计、报告

## 安装

### 1. 安装依赖

```bash
pip install pyyaml click rich watchdog
```

### 2. 验证安装

```bash
python ~/.claude/skills-management/cli/main.py --version
```

## 使用方法

### 基本命令

```bash
# 列出所有技能
python ~/.claude/skills-management/cli/main.py list

# 查看技能详情
python ~/.claude/skills-management/cli/main.py info <skill-name>

# 搜索技能
python ~/.claude/skills-management/cli/main.py search <query>

# 查看使用统计
python ~/.claude/skills-management/cli/main.py stats

# 扫描新技能
python ~/.claude/skills-management/cli/main.py discovery

# 同步注册表
python ~/.claude/skills-management/cli/main.py sync

# 生成报告
python ~/.claude/skills-management/cli/main.py report

# 配置使用追踪（自动追踪技能调用）
python ~/.claude/skills-management/cli/main.py hook-setup
```

> **注意**: `hook-setup` 会自动配置 Claude Code 的钩子，使系统能够自动追踪技能的使用情况。配置后需要**重启 Claude Code** 使钩子生效。

### Windows 快捷方式

使用提供的批处理文件：

```bash
# 复制 skills.bat 到 PATH 中的目录
copy C:\Users\roucy\.claude\skills-management\skills.bat C:\Windows\System32\

# 然后可以直接使用
skills list
skills stats
skills discovery
```

## 配置

配置文件位置：`~/.claude/skills-management/data/config.yaml`

### 默认扫描路径

```yaml
discovery:
  scan_paths:
    # 本地插件
    - path: ~/.claude/plugins/local/skills
      type: local

    # NPM 全局
    - path: ~/.claude/node_modules
      type: npm_global

    # NPM 本地
    - path: ./node_modules
      type: npm_local

    # 项目技能
    - path: ./.claude/skills
      type: project
```

## 自动发现机制

系统会自动发现以下方式创建的技能：

1. **手动创建** - 在 `~/.claude/plugins/local/skills/` 创建 SKILL.md
2. **NPM 安装** - `npm install -g @your-org/skill`
3. **项目本地** - 在项目目录的 `./.claude/skills/` 创建
4. **Git 克隆** - 克隆包含技能的仓库

### 使用追踪（Hook 机制）

系统通过 Claude Code 的钩子自动追踪技能使用情况：

- `UserPromptExpansion` - 捕获技能调用开始（slash command）
- `PreToolUse` - 捕获 Skill 工具调用开始
- `PostToolUse` - 捕获 Skill 工具调用完成（记录成功/失败）

#### 配置使用追踪

```bash
# 运行一次即可自动配置 Claude Code 钩子
python ~/.claude/skills-management/cli/main.py hook-setup
```

配置后，每次使用技能都会自动记录到 `skills_usage.yaml`。

**追踪的信息**：
- 技能名称
- 使用时间
- 持续时间
- 成功/失败状态
- 使用趋势

### 技能文件格式

```markdown
---
name: my-skill
description: 我的技能描述
tags: [utility, helper]
version: "1.0.0"
---

技能内容...
```

## 数据管理

### 冷热数据分离

- **热数据 (0-2月)**: 常驻内存，快速访问
- **温数据 (2-6月)**: 归档存储，按需加载
- **冷数据 (6月+)**: 压缩存储，用于历史分析

### 自动归档

系统每天凌晨2点自动归档旧数据：
- 超过2个月的数据移到 warm/
- 超过6个月的数据压缩到 cold/

## 工作流程

### 1. 首次使用

```bash
# 扫描现有技能
python ~/.claude/skills-management/cli/main.py discovery

# 查看所有技能
python ~/.claude/skills-management/cli/main.py list

# 查看统计
python ~/.claude/skills-management/cli/main.py stats
```

### 2. 日常使用

```bash
# 创建新技能后，自动发现
mkdir -p ~/.claude/plugins/local/skills/my-tool
cat > ~/.claude/plugins/local/skills/my-tool/SKILL.md << 'EOF'
---
name: my-tool
description: 我的工具
tags: [utility]
---
EOF

# 扫描新技能
python ~/.claude/skills-management/cli/main.py discovery

# 查看新技能
python ~/.claude/skills-management/cli/main.py info my-tool
```

### 3. 定期维护

```bash
# 同步注册表
python ~/.claude/skills-management/cli/main.py sync

# 生成使用报告
python ~/.claude/skills-management/cli/main.py report --output report.md

# 验证数据完整性
python ~/.claude/skills-management/cli/main.py validate
```

## 目录结构

```
~/.claude/skills-management/
├── core/                   # 核心组件
│   ├── config.py          # 配置管理
│   ├── skill_registry.py  # 技能注册表
│   ├── usage_tracker.py   # 使用追踪器
│   ├── scanner.py         # 扫描器
│   └── npm_scanner.py     # NPM扫描器
├── cli/                   # CLI接口
│   └── main.py           # 主入口
├── data/                  # 数据存储
│   ├── hot/              # 热数据
│   ├── warm/             # 温数据
│   └── cold/             # 冷数据
├── reports/              # 报告输出
└── scripts/              # 脚本
    ├── install.sh        # 安装脚本
    └── install.bat       # Windows安装脚本
```

## 常见问题

### Q: 如何创建新技能？

A: 在配置的扫描路径下创建包含 SKILL.md 的目录，然后运行 `skills discovery`。

### Q: 技能没有被发现？

A: 
1. 检查 SKILL.md 文件格式是否正确
2. 确认路径在配置的 scan_paths 中
3. 运行 `skills discovery` 手动扫描
4. 查看扫描状态：`skills discovery-status`

### Q: 如何禁用文件监控？

A: 在配置文件中设置 `discovery.scan_frequency: manual`

### Q: 数据存储在哪里？

A: 
- 热数据：`~/.claude/skills-management/data/hot/`
- 温数据：`~/.claude/skills-management/data/warm/`
- 冷数据：`~/.claude/skills-management/data/cold/`

### Q: 如何备份技能数据？

A: 备制整个 `~/.claude/skills-management/` 目录

## 系统要求

- Python 3.7+
- pyyaml
- click
- rich
- watchdog (可选，用于文件监控)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**版本**: 1.0.0  
**最后更新**: 2026-05-04
