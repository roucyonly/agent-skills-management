# Skills Management System - 验证机制说明

## 问题

用户提出了一个很好的问题：**NPM 扫描器会扫描所有 npm 包，但如何确保只有真正的技能被注册？**

## 解决方案：技能验证器

### 新增验证机制

我们已经添加了完整的验证系统，确保只有真正的 Claude Code 技能被注册到系统中。

### 验证流程

```
npm 包扫描
    ↓
找到 SKILL.md 文件
    ↓
技能验证器检查
    ↓
┌─────────────────────────────────────────────────────────────┐
│  验证步骤                                               │
│  1. 检查文件是否存在                                   │
│  2. 解析 frontmatter（YAML 格式）                       │
│  3. 验证必需字段：                                     │
│     ✓ name (必需)                                     │
│     ✓ description (推荐)                               │
│  4. 验证字段类型和值：                                 │
│     ✓ name: 非空字符串                                │
│     ✓ tags: 列表                                      │
│     ✓ complexity: low/medium/high                      │
│     ✓ version: 字符串                                  │
│  5. 检查内容长度（至少10个字符）                        │
│  6. NPM 包特殊验证：                                   │
│     ✓ 检查包名是否在忽略列表中                         │
│     ✓ 启发式判断是否是技能包                           │
└─────────────────────────────────────────────────────────────┘
    ↓
通过验证 → 注册到系统
未通过 → 跳过并记录原因
```

## 验证规则详解

### 1. 文件格式验证

**必须满足**：
- 文件名：`SKILL.md`（推荐，但允许其他名称）
- Frontmatter 格式：正确的 YAML 格式
- 必需字段：`name`

**示例**：
```markdown
---
name: my-skill              # 必需
description: 我的技能        # 推荐
tags: [utility, helper]     # 推荐
version: "1.0.0"           # 推荐
complexity: low            # 可选：low/medium/high
---

技能内容...
```

### 2. 字段验证

| 字段 | 类型 | 必需 | 验证规则 |
|------|------|------|----------|
| `name` | string | ✅ | 非空字符串 |
| `description` | string | ❌ | 字符串类型 |
| `tags` | list | ❌ | 列表，元素为字符串 |
| `version` | string | ❌ | 字符串类型 |
| `complexity` | enum | ❌ | low/medium/high |
| `tech_stack` | list | ❌ | 列表，元素为字符串 |
| `scenarios` | list | ❌ | 列表，元素为字符串 |

### 3. NPM 包特殊验证

#### 启发式规则

系统使用启发式规则判断 npm 包是否是技能：

**明确的非技能包（会被忽略）**：
```
- react, vue, angular, jquery, lodash
- express, koa, fastify
- babel, webpack, vite
- eslint, prettier, jest
- typescript, ts-node
```

**可能的技能包（会被检查）**：
```
- 包名包含：skill, claude, agent, assistant, helper, tool
- 描述包含：claude code, claude skill, ai assistant, agent skill
- 有完整的 frontmatter 和 tags
- 有 scenarios 字段
```

#### 忽略列表配置

在 `config.yaml` 中配置：

```yaml
discovery:
  npm_ignore_patterns:
    - react
    - vue
    - angular
    - jquery
    - lodash
    - express
    - koa
    - fastify
    - babel
    - webpack
    - vite
    - eslint
    - prettier
    - jest
    - typescript
    - ts-node
```

## 使用示例

### 验证单个技能文件

```bash
# 验证技能文件
python ~/.claude/skills-management/cli/main.py validate /path/to/SKILL.md

# 输出示例：
OK /path/to/SKILL.md is a valid skill file

Skill Name: my-skill
Description: 我的技能
Tags: utility, helper
```

### 验证整个注册表

```bash
# 验证注册表中的所有技能
python ~/.claude/skills-management/cli/main.py validate

# 输出示例：
✓ 注册表验证通过
```

### 扫描 npm 包

```bash
# 扫描 npm 包并显示发现的技能
python ~/.claude/skills-management/cli/main.py npm-scan

# 输出示例：
扫描全局 npm 包...

发现 2 个 npm 技能包:

✓ @my-org/frontend-helper
  包名: @my-org/frontend-helper
  版本: 1.2.0
  路径: ~/node_modules/@my-org/frontend-helper/SKILL.md

✓ @my-org/code-review
  包名: @my-org/code-review
  版本: 2.0.0
  路径: ~/node_modules/@my-org/code-review/SKILL.md
```

## 验证失败的常见原因

### 1. 缺少必需字段

```
X SKILL.md is not a valid skill file
Reason: 缺少必需字段: name
```

**解决**：在 frontmatter 中添加 `name` 字段

### 2. 字段类型错误

```
X SKILL.md is not a valid skill file
Reason: tags 必须是列表
```

**解决**：确保 `tags` 是列表格式
```yaml
tags: [utility, helper]  # 正确
tags: utility, helper     # 错误
```

### 3. complexity 值无效

```
X SKILL.md is not a valid skill file
Reason: complexity 必须是以下值之一: ['low', 'medium', 'high']
```

**解决**：使用有效的 complexity 值
```yaml
complexity: low      # 正确
complexity: beginner  # 错误
```

### 4. 内容太短

```
X SKILL.md is not a valid skill file
Reason: 技能内容太短或为空
```

**解决**：确保内容至少有 10 个字符

## 配置选项

### 启用/禁用 NPM 启发式规则

```yaml
discovery:
  enable_npm_heuristics: true  # 启用启发式判断
```

### 自定义忽略列表

```yaml
discovery:
  npm_ignore_patterns:
    - your-package-name
    - another-package
```

### 调整验证严格度

```yaml
discovery:
  require_validation: true  # 必须通过验证才能注册
```

## 测试验证功能

### 创建测试技能

```bash
# 1. 创建测试技能
mkdir -p ~/.claude/plugins/local/skills/test-skill

# 2. 创建有效的 SKILL.md
cat > ~/.claude/plugins/local/skills/test-skill/SKILL.md << 'EOF'
---
name: test-skill
description: 测试技能
tags: [test]
version: "1.0.0"
complexity: low
---

这是一个测试技能
EOF

# 3. 验证
python ~/.claude/skills-management/cli/main.py validate ~/.claude/plugins/local/skills/test-skill/SKILL.md

# 输出：
# OK ... is a valid skill file
```

### 创建无效技能测试

```bash
# 1. 创建无效的 SKILL.md（缺少 name）
cat > ~/.claude/plugins/local/skills/invalid-skill/SKILL.md << 'EOF'
---
description: 无效技能
tags: [test]
---
EOF

# 2. 验证
python ~/.claude/skills-management/cli/main.py validate ~/.claude/plugins/local/skills/invalid-skill/SKILL.md

# 输出：
# X ... is not a valid skill file
# Reason: 缺少必需字段: name
```

## 扫描过程中的验证

### 自动验证

```bash
# 运行扫描
python ~/.claude/skills-management/cli/main.py discovery --verbose

# 输出：
扫描技能路径...
  ✓ 注册: example-skill
  ✗ 无效: invalid-skill.md - 缺少必需字段: name

扫描完成:
  扫描路径: 2
  发现技能: 1
  新注册: 1
  更新: 0
  跳过: 1
```

### NPM 扫描示例

```bash
# 运行 npm 扫描
python ~/.claude/skills-management/cli/main.py npm-scan

# 输出：
扫描全局 npm 包...

扫描了 150 个 npm 包
- 通过验证: 2 个
- 被忽略: 148 个（常见的库/工具包）
- 验证失败: 0 个

发现 2 个 npm 技能包:
```

## 总结

### ✅ 验证机制的好处

1. **准确性**：只有真正的技能被注册
2. **防止污染**：过滤掉普通的 npm 包
3. **质量控制**：确保技能文件格式正确
4. **灵活配置**：可自定义忽略规则
5. **详细反馈**：显示验证失败的原因

### 🎯 验证流程

```
扫描文件 → 验证格式 → 检查字段 → NPM特殊验证 → 通过 → 注册
                    ↓
                   失败 → 跳过并记录原因
```

### 📊 验证统计

系统会跟踪：
- 扫描的文件总数
- 通过验证的技能数
- 被忽略的包数
- 验证失败的文件数及原因

---

**现在系统会正确验证每个 npm 包，确保只有真正的技能被注册！** ✅

---

**文档版本**: 1.0  
**最后更新**: 2026-05-04  
**状态**: 已实现
