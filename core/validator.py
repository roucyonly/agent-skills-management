"""
技能验证器
验证文件是否是有效的 Claude Code 技能
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple


class SkillValidator:
    """技能验证器"""

    def __init__(self, config):
        self.config = config

    def validate_skill_file(self, skill_file: Path) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        验证技能文件是否有效

        Returns:
            (is_valid, error_message, skill_data)
        """
        if not skill_file.exists():
            return False, f"文件不存在: {skill_file}", None

        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, f"无法读取文件: {e}", None

        # 检查文件名
        if skill_file.name != 'SKILL.md':
            # 允许，但发出警告
            pass

        # 解析 frontmatter
        frontmatter, skill_content = self._parse_frontmatter(content)

        if frontmatter is None:
            return False, "缺少或无效的 frontmatter", None

        # 验证必需字段
        required_fields = ['name']
        for field in required_fields:
            if field not in frontmatter:
                return False, f"缺少必需字段: {field}", None

        # 验证字段类型和值
        validation_result = self._validate_frontmatter_fields(frontmatter)
        if not validation_result[0]:
            return False, validation_result[1], None

        # 检查内容是否为空
        if not skill_content or len(skill_content.strip()) < 10:
            return False, "技能内容太短或为空", None

        # 提取技能数据
        skill_data = {
            'name': frontmatter.get('name'),
            'display_name': frontmatter.get('description', frontmatter.get('name')),
            'description': frontmatter.get('description', ''),
            'path': str(skill_file),
            'tags': frontmatter.get('tags', []),
            'tech_stack': frontmatter.get('tech_stack', []),
            'scenarios': frontmatter.get('scenarios', []),
            'complexity': frontmatter.get('complexity', 'medium'),
            'version': frontmatter.get('version', '1.0.0'),
            'frontmatter': frontmatter,
            'content': skill_content
        }

        return True, None, skill_data

    def _parse_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """
        解析 frontmatter 和内容

        Returns:
            (frontmatter, content)
        """
        if not content.startswith('---'):
            return None, content

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None, content

        try:
            frontmatter = yaml.safe_load(parts[1])
            skill_content = parts[2]
            return frontmatter, skill_content
        except Exception:
            return None, content

    def _validate_frontmatter_fields(self, frontmatter: Dict) -> Tuple[bool, Optional[str]]:
        """
        验证 frontmatter 字段

        Returns:
            (is_valid, error_message)
        """
        # 验证 name
        if 'name' in frontmatter:
            name = frontmatter['name']
            if not isinstance(name, str) or not name.strip():
                return False, "name 必须是非空字符串"

        # 验证 description
        if 'description' in frontmatter:
            description = frontmatter['description']
            if not isinstance(description, str):
                return False, "description 必须是字符串"

        # 验证 tags
        if 'tags' in frontmatter:
            tags = frontmatter['tags']
            if not isinstance(tags, list):
                return False, "tags 必须是列表"
            if not all(isinstance(tag, str) for tag in tags):
                return False, "tags 中的所有元素必须是字符串"

        # 验证 version
        if 'version' in frontmatter:
            version = frontmatter['version']
            if not isinstance(version, str):
                return False, "version 必须是字符串"

        # 验证 complexity
        if 'complexity' in frontmatter:
            complexity = frontmatter['complexity']
            valid_values = ['low', 'medium', 'high']
            if complexity not in valid_values:
                return False, f"complexity 必须是以下值之一: {valid_values}"

        return True, None

    def is_npm_package_skill(self, package_name: str, skill_path: Path) -> bool:
        """
        判断 npm 包是否是真正的技能

        通过以下条件判断：
        1. SKILL.md 文件存在且有效
        2. 包名符合技能命名规范（可选）
        3. 不在忽略列表中
        """
        # 1. 验证 SKILL.md
        is_valid, error_msg, skill_data = self.validate_skill_file(skill_path)
        if not is_valid:
            return False

        # 2. 检查是否在忽略列表中
        if self._is_package_ignored(package_name):
            return False

        # 3. 检查包名模式（可选启发式规则）
        if self.config.get('discovery.enable_npm_heuristics', True):
            if not self._looks_like_skill_package(package_name, skill_data):
                return False

        return True

    def _is_package_ignored(self, package_name: str) -> bool:
        """检查包是否在忽略列表中"""
        ignore_patterns = self.config.get('discovery.npm_ignore_patterns', [])

        for pattern in ignore_patterns:
            if pattern in package_name.lower():
                return True

        return False

    def _looks_like_skill_package(self, package_name: str, skill_data: Dict) -> bool:
        """
        启发式判断：检查包是否看起来像技能

        Rules:
        1. 包名包含 'skill', 'claude', 'agent' 等关键词 → 可能是技能
        2. 包的描述包含 'claude code', 'skill', 'agent' → 可能是技能
        3. SKILL.md 有完整的 frontmatter → 可能是技能
        4. 明显的库/工具包名 → 可能不是技能
        """
        # 明确不是技能的包名模式
        non_skill_patterns = [
            'react', 'vue', 'angular', 'jquery', 'lodash',
            'express', 'koa', 'fastify',
            'babel', 'webpack', 'vite',
            'eslint', 'prettier', 'jest',
            'typescript', 'typescript'
        ]

        package_lower = package_name.lower()
        for pattern in non_skill_patterns:
            if pattern in package_lower:
                # 除非有明确的 frontmatter 说明这是技能
                if skill_data.get('tags'):
                    # 如果有 tags，更可能是技能
                    return True
                return False

        # 可能是技能的包名模式
        skill_keywords = ['skill', 'claude', 'agent', 'assistant', 'helper', 'tool']
        if any(keyword in package_lower for keyword in skill_keywords):
            return True

        # 检查描述
        description = skill_data.get('description', '').lower()
        skill_desc_keywords = ['claude code', 'claude skill', 'ai assistant', 'agent skill']
        if any(keyword in description for keyword in skill_desc_keywords):
            return True

        # 检查 tags
        tags = [tag.lower() for tag in skill_data.get('tags', [])]
        if tags:
            # 有 tags 的更可能是技能
            return True

        # 检查 scenarios
        scenarios = skill_data.get('scenarios', [])
        if scenarios:
            # 有 scenarios 的更可能是技能
            return True

        # 默认情况下，如果有有效的 SKILL.md，就认为是技能
        return True
