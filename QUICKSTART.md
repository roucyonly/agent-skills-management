# Skills Management System - 快速开始指南

## 5分钟快速上手

### 第1步：安装依赖

```bash
pip install pyyaml click rich watchdog
```

### 第2步：验证安装

```bash
python ~/.claude/skills-management/cli/main.py --version
```

应该看到：`main.py, version 1.0.0`

### 第3步：扫描现有技能

```bash
python ~/.claude/skills-management/cli/main.py discovery
```

这会扫描所有配置的路径，自动发现技能。

### 第4步：查看技能列表

```bash
python ~/.claude/skills-management/cli/main.py list
```

### 第5步：查看使用统计

```bash
python ~/.claude/skills-management/cli/main.py stats
```

## 创建你的第一个技能

### 1. 创建技能目录

```bash
mkdir -p ~/.claude/plugins/local/skills/hello-world
```

### 2. 创建 SKILL.md

```bash
cat > ~/.claude/plugins/local/skills/hello-world/SKILL.md << 'EOF'
---
name: hello-world
description: 我的第一个技能
tags: [example, demo]
version: "1.0.0"
---

这是一个示例技能，用于演示技能管理系统。

## 使用方法

当用户请求帮助时，这个技能会提供友好的问候。

## 功能

- 打招呼
- 提供帮助
- 展示技能系统的使用
EOF
```

### 3. 扫描新技能

```bash
python ~/.claude/skills-management/cli/main.py discovery
```

你会看到：

```
🎉 发现新技能
名称: hello-world
描述: 我的第一个技能
路径: ~/.claude/plugins/local/skills/hello-world/SKILL.md
来源: local

已自动注册到技能管理系统
```

### 4. 查看技能详情

```bash
python ~/.claude/skills-management/cli/main.py info hello-world
```

## 日常使用技巧

### 技能发现

系统支持多种安装方式：

```bash
# 方式1：手动创建
mkdir -p ~/.claude/plugins/local/skills/my-skill
# 创建 SKILL.md

# 方式2：NPM 全局安装
npm install -g @your-org/skill

# 方式3：项目本地
cd ~/my-project
mkdir -p .claude/skills/project-skill
# 创建 SKILL.md
```

创建后运行：
```bash
python ~/.claude/skills-management/cli/main.py discovery
```

### 搜索技能

```bash
# 按名称搜索
python ~/.claude/skills-management/cli/main.py search frontend

# 查看所有技能
python ~/.claude/skills-management/cli/main.py list

# 按标签过滤
python ~/.claude/skills-management/cli/main.py list --filter-tag utility
```

### 查看统计

```bash
# 默认30天统计
python ~/.claude/skills-management/cli/main.py stats

# 指定周期
python ~/.claude/skills-management/cli/main.py stats --period 7

# 显示更多热门技能
python ~/.claude/skills-management/cli/main.py stats --top 20
```

### 生成报告

```bash
# 查看报告
python ~/.claude/skills-management/cli/main.py report

# 保存报告
python ~/.claude/skills-management/cli/main.py report --output report.md
```

## Windows 优化

### 创建快捷命令

创建 `C:\Windows\System32\skills.bat`：

```batch
@echo off
python C:\Users\roucy\.claude\skills-management\cli\main.py %*
```

然后可以直接使用：

```bash
skills list
skills stats
skills discovery
```

### 添加到 PATH

将 `C:\Users\roucy\.claude\skills-management` 添加到系统 PATH，然后：

```bash
skills.bat list
skills.bat stats
skills.bat discovery
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `skills list` | 列出所有技能 |
| `skills info <name>` | 查看技能详情 |
| `skills search <query>` | 搜索技能 |
| `skills stats` | 查看使用统计 |
| `skills discovery` | 扫描新技能 |
| `skills sync` | 同步注册表 |
| `skills report` | 生成报告 |
| `skills validate` | 验证数据 |

## 配置自定义

编辑配置文件：

```bash
# Windows
notepad C:\Users\roucy\.claude\skills-management\data\config.yaml

# Linux/Mac
nano ~/.claude/skills-management/data/config.yaml
```

### 添加新的扫描路径

```yaml
discovery:
  scan_paths:
    - path: /custom/path/to/skills
      type: custom
      recursive: true
      skill_pattern: '*/SKILL.md'
```

修改后运行：
```bash
python ~/.claude/skills-management/cli/main.py discovery
```

## 故障排查

### 问题：技能没有被发现

```bash
# 检查路径配置
python ~/.claude/skills-management/cli/main.py discovery-status

# 手动扫描并显示详细信息
python ~/.claude/skills-management/cli/main.py discovery --verbose
```

### 问题：编码错误

Windows 用户如果看到编码错误，使用：

```bash
chcp 65001
python ~/.claude/skills-management/cli/main.py list
```

### 问题：找不到 Python

确保 Python 在 PATH 中：

```bash
# Windows
where python

# Linux/Mac
which python
```

## 下一步

- 📖 阅读完整文档：`README.md`
- 🔧 自定义配置：编辑 `config.yaml`
- 📊 查看使用报告：`skills report --output report.md`
- 🎯 创建更多技能：在扫描路径下创建 SKILL.md

## 获取帮助

遇到问题？

1. 查看配置文件：`~/.claude/skills-management/data/config.yaml`
2. 运行验证：`python ~/.claude/skills-management/cli/main.py validate`
3. 查看日志：检查控制台输出

---

**祝你使用愉快！** 🎉
