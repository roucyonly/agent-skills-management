# Skills Management System - CLI 手动配置方案

## 设计变更

### ❌ 之前的错误设计
- **自动检测**: 系统自动扫描所有 npm 包的 `package.json`
- **问题**:
  - 检测到太多无关的 CLI 工具
  - 无法区分哪些 CLI 工具是有用的
  - 缺乏如何使用 CLI 的详细说明
  - Agent 不知道何时以及如何调用这些 CLI

### ✅ 现在的正确设计
- **手动配置**: 通过创建 `SKILL.md` 文件手动配置 CLI 工具
- **优势**:
  - 收敛可控：只包含用户明确配置的技能
  - 详细文档：SKILL.md 包含完整的使用说明
  - Agent 可理解：通过 skill_understanding 系统提取能力
  - 灵活性高：用户决定如何使用 CLI 工具

## 系统现状

### 支持的技能格式

1. **SKILL.md** - 标准技能定义
   - 位置: `~/.claude/plugins/local/skills/*/SKILL.md`
   - 用途: 定义具体技能和工具使用方法

2. **CLAUDE.md** - 项目级配置
   - 位置: `./CLAUDE.md` 或 `./claude.md`
   - 用途: 项目特定的技能和约定

3. **AGENT.md** - Agent 定义
   - 位置: `./AGENT.md` 或 `./agent.md`
   - 用途: 定义自主 Agent 的行为和能力

### 已移除的格式

❌ **package.json 自动检测** - 不再自动扫描 npm 包
- 原因: 收敛性差，包含太多无关工具
- 替代方案: 手动创建 SKILL.md 文件

## 使用示例

### 为 Playwright CLI 创建技能

创建了 `web-automation` 技能作为示例：

**位置**: `~/.claude/plugins/local/skills/web-automation/SKILL.md`

**内容包含**:
- 前置条件（如何安装 Playwright CLI）
- 能力列表（浏览器控制、元素交互等）
- 使用模式（基本导航、表单填写等）
- 代码示例
- 何时使用的指导
- 故障排除

### 查看技能信息

```bash
# 列出所有技能
python ~/.claude/skills-management/cli/main.py list

# 查看技能详情
python ~/.claude/skills-management/cli/main.py info web-automation

# 查看技能理解信息
python ~/.claude/skills-management/cli/main.py understand web-automation
```

## 技能理解系统

### 如何工作

1. **自动生成**: 当发现新技能时，系统自动生成理解信息
2. **结构化提取**: 从 SKILL.md 中提取：
   - Capabilities（能力）
   - Usage patterns（使用模式）
   - Invocation methods（调用方式）
   - When to use（何时使用）

3. **Agent 友好**: 提供结构化的信息，便于 Agent 理解和调用

### 示例：web-automation 技能理解

```
技能: web-automation
类型: skill_md

能力:
  - Automated browser testing
  - Web scraping and data extraction
  - Form automation and submission
  - Screenshot capture and PDF generation
  - Page interaction and navigation

使用模式:
  - Automated browser testing
  - Web scraping and data extraction
  - Form automation and submission
  - Screenshot capture and PDF generation
  - Page interaction and navigation
```

## 如何添加新的 CLI 工具技能

### 步骤

1. **创建技能目录**
   ```bash
   mkdir -p ~/.claude/plugins/local/skills/my-tool
   ```

2. **创建 SKILL.md 文件**
   ```bash
   touch ~/.claude/plugins/local/skills/my-tool/SKILL.md
   ```

3. **编写技能定义**
   ```yaml
   ---
   name: my-tool
   description: Brief description of what the tool does
   tags: [tool, category, cli]
   tech_stack: [language, dependencies]
   scenarios:
     - Use case 1
     - Use case 2
   complexity: low|medium|high
   version: "1.0.0"
   ---

   # My Tool Skill

   Detailed documentation...
   ```

4. **运行 discovery**
   ```bash
   python ~/.claude/skills-management/cli/main.py discovery
   ```

5. **验证技能**
   ```bash
   python ~/.claude/skills-management/cli/main.py info my-tool
   python ~/.claude/skills-management/cli/main.py understand my-tool
   ```

### SKILL.md 模板

```yaml
---
name: skill-name
description: One-line description
tags: [tag1, tag2, tag3]
tech_stack: [tool1, tool2]
scenarios:
  - Scenario 1
  - Scenario 2
complexity: low|medium|high
version: "1.0.0"
---

# Skill Title

Detailed description of the skill.

## Prerequisites

How to install the tool or dependencies.

## Capabilities

List what the skill can do.

## Usage Patterns

### Pattern 1
```bash
command example
```

### Pattern 2
```bash
command example
```

## When to Use

- Situation 1
- Situation 2

## Examples

Detailed usage examples...

## Troubleshooting

Common issues and solutions...

## Quick Reference

| Action | Command |
|--------|---------|
| Action 1 | `command 1` |
| Action 2 | `command 2` |
```

## 系统架构

### 技能生命周期

```
创建 SKILL.md
    ↓
Discovery 扫描
    ↓
解析器解析 (parsers.py)
    ↓
注册到系统 (skill_registry.py)
    ↓
生成理解信息 (skill_understanding.py)
    ↓
Agent 可查询和使用
```

### 关键组件

1. **parsers.py** - 解析不同格式的技能文件
2. **skill_registry.py** - 技能注册和存储
3. **skill_understanding.py** - 生成技能理解信息
4. **scanner.py** - 自动发现新技能

## 配置文件

**位置**: `~/.claude/skills-management/data/config.yaml`

**扫描路径配置**:
```yaml
discovery:
  scan_paths:
  - path: ~/.claude/plugins/local/skills
    recursive: true
    skill_patterns:
    - '*/SKILL.md'
    type: local
  - path: .
    recursive: false
    skill_patterns:
    - CLAUDE.md
    - claude.md
    - AGENT.md
    - agent.md
    type: project
```

## 总结

### ✅ 优势

1. **收敛可控**: 只包含用户明确配置的技能
2. **详细文档**: SKILL.md 提供完整的使用说明
3. **Agent 可理解**: 结构化的理解信息
4. **易于维护**: 手动管理，清晰明确

### 🎯 适用场景

- 需要使用特定的 CLI 工具
- 想要为 Agent 提供工具使用能力
- 需要详细的使用文档和示例
- 希望技能集合收敛可控

### 📝 最佳实践

1. **一个工具一个技能**: 为每个 CLI 工具创建独立的 SKILL.md
2. **详细文档**: 包含前置条件、使用示例、故障排除
3. **清晰命名**: 使用描述性的技能名称
4. **合理标签**: 帮助分类和搜索
5. **保持更新**: 当工具更新时及时更新 SKILL.md

---

**更新时间**: 2026-05-04
**状态**: ✅ CLI 手动配置方案已实现
