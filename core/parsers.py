"""
技能解析器
支持不同格式的技能文件解析
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple, List


class BaseParser:
    """基础解析器"""

    def __init__(self, config):
        self.config = config

    def parse(self, file_path: Path) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        解析文件

        Returns:
            (is_valid, error_message, skill_data)
        """
        raise NotImplementedError


class SkillMDParser(BaseParser):
    """SKILL.md 格式解析器"""

    def parse(self, file_path: Path) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """解析 SKILL.md 文件"""
        if not file_path.exists():
            return False, f"文件不存在: {file_path}", None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, f"无法读取文件: {e}", None

        # 解析 frontmatter
        frontmatter, skill_content = self._parse_frontmatter(content)

        if frontmatter is None:
            return False, "缺少或无效的 frontmatter", None

        # 验证必需字段
        if 'name' not in frontmatter:
            return False, "缺少必需字段: name", None

        # 提取技能数据
        skill_data = {
            'name': frontmatter.get('name'),
            'display_name': frontmatter.get('description', frontmatter.get('name')),
            'description': frontmatter.get('description', ''),
            'path': str(file_path),
            'tags': frontmatter.get('tags', []),
            'tech_stack': frontmatter.get('tech_stack', []),
            'scenarios': frontmatter.get('scenarios', []),
            'complexity': frontmatter.get('complexity', 'medium'),
            'version': frontmatter.get('version', '1.0.0'),
            'skill_type': 'skill_md',
            'frontmatter': frontmatter,
            'content': skill_content
        }

        return True, None, skill_data

    def _parse_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """解析 frontmatter 和内容"""
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


class ClaudeMDParser(BaseParser):
    """CLAUDE.md 格式解析器"""

    def parse(self, file_path: Path) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """解析 CLAUDE.md 文件"""
        if not file_path.exists():
            return False, f"文件不存在: {file_path}", None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, f"无法读取文件: {e}", None

        # 解析 frontmatter
        frontmatter, skill_content = self._parse_frontmatter(content)

        # 提取项目名称
        project_name = file_path.parent.name

        # 如果没有 frontmatter，创建默认的
        if frontmatter is None:
            frontmatter = {}

        # 生成技能数据
        skill_data = {
            'name': f"claude-{project_name}",
            'display_name': frontmatter.get('title', f"{project_name} Project"),
            'description': frontmatter.get('description', f"Project-specific skills for {project_name}"),
            'path': str(file_path),
            'tags': frontmatter.get('tags', ['project', 'claude-config']),
            'tech_stack': frontmatter.get('tech_stack', []),
            'scenarios': frontmatter.get('scenarios', []),
            'complexity': frontmatter.get('complexity', 'medium'),
            'version': frontmatter.get('version', '1.0.0'),
            'skill_type': 'claude_md',
            'project_context': self._extract_project_context(content),
            'frontmatter': frontmatter,
            'content': skill_content
        }

        return True, None, skill_data

    def _parse_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """解析 frontmatter 和内容"""
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

    def _extract_project_context(self, content: str) -> Dict:
        """从内容中提取项目上下文"""
        context = {
            'has_architecture': False,
            'has_commands': False,
            'has_patterns': False,
            'key_topics': []
        }

        # 检查常见的关键词
        keywords = {
            'architecture': ['architecture', 'design', 'structure', 'components'],
            'commands': ['command', 'script', 'build', 'test', 'deploy'],
            'patterns': ['pattern', 'convention', 'style', 'guideline']
        }

        content_lower = content.lower()

        for category, words in keywords.items():
            if any(word in content_lower for word in words):
                if category == 'architecture':
                    context['has_architecture'] = True
                elif category == 'commands':
                    context['has_commands'] = True
                elif category == 'patterns':
                    context['has_patterns'] = True

        return context


class AgentMDParser(BaseParser):
    """AGENT.md 格式解析器"""

    def parse(self, file_path: Path) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """解析 AGENT.md 文件"""
        if not file_path.exists():
            return False, f"文件不存在: {file_path}", None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, f"无法读取文件: {e}", None

        # 解析 frontmatter
        frontmatter, agent_content = self._parse_frontmatter(content)

        # 提取 agent 名称
        agent_name = file_path.parent.name

        # 如果没有 frontmatter，创建默认的
        if frontmatter is None:
            frontmatter = {}

        # 提取 agent 能力
        capabilities = self._extract_capabilities(content)

        # 生成技能数据
        skill_data = {
            'name': f"agent-{agent_name}",
            'display_name': frontmatter.get('title', f"{agent_name} Agent"),
            'description': frontmatter.get('description', f"Agent definition for {agent_name}"),
            'path': str(file_path),
            'tags': frontmatter.get('tags', ['agent', 'autonomous']),
            'tech_stack': frontmatter.get('tech_stack', []),
            'scenarios': frontmatter.get('scenarios', []),
            'complexity': frontmatter.get('complexity', 'high'),
            'version': frontmatter.get('version', '1.0.0'),
            'skill_type': 'agent_md',
            'capabilities': capabilities,
            'agent_type': self._detect_agent_type(content),
            'frontmatter': frontmatter,
            'content': agent_content
        }

        return True, None, skill_data

    def _parse_frontmatter(self, content: str) -> Tuple[Optional[Dict], str]:
        """解析 frontmatter 和内容"""
        if not content.startswith('---'):
            return None, content

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None, content

        try:
            frontmatter = yaml.safe_load(parts[1])
            agent_content = parts[2]
            return frontmatter, agent_content
        except Exception:
            return None, content

    def _extract_capabilities(self, content: str) -> Dict:
        """从内容中提取 agent 能力"""
        capabilities = {
            'can_use_tools': False,
            'can_write_code': False,
            'can_run_commands': False,
            'can_search_web': False,
            'autonomous': False
        }

        content_lower = content.lower()

        # 检测能力关键词
        capability_keywords = {
            'can_use_tools': ['tool', 'function', 'api'],
            'can_write_code': ['code', 'programming', 'development'],
            'can_run_commands': ['command', 'execute', 'bash', 'shell'],
            'can_search_web': ['web', 'search', 'browse'],
            'autonomous': ['autonomous', 'independent', 'self-directed']
        }

        for capability, keywords in capability_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                capabilities[capability] = True

        return capabilities

    def _detect_agent_type(self, content: str) -> str:
        """检测 agent 类型"""
        content_lower = content.lower()

        if 'general-purpose' in content_lower or 'general purpose' in content_lower:
            return 'general-purpose'
        elif 'explore' in content_lower:
            return 'explore'
        elif 'plan' in content_lower:
            return 'plan'
        elif 'claude-code-guide' in content_lower:
            return 'claude-code-guide'
        else:
            return 'custom'


class ParserFactory:
    """解析器工厂"""

    def __init__(self, config):
        self.config = config
        self.parsers = {
            'skill_md': SkillMDParser(config),
            'claude_md': ClaudeMDParser(config),
            'agent_md': AgentMDParser(config)
        }

    def get_parser(self, file_path: Path, skill_type: str = None) -> Optional[BaseParser]:
        """根据文件类型获取解析器"""
        file_name = file_path.name

        # 如果指定了 skill_type，直接返回对应的解析器
        if skill_type:
            return self.parsers.get(skill_type)

        # 根据文件名自动检测
        if file_name in ['SKILL.md', 'skill.md']:
            return self.parsers['skill_md']
        elif file_name in ['CLAUDE.md', 'claude.md']:
            return self.parsers['claude_md']
        elif file_name in ['AGENT.md', 'agent.md']:
            return self.parsers['agent_md']

        return None

    def parse_file(self, file_path: Path, skill_type: str = None) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """自动解析文件"""
        parser = self.get_parser(file_path, skill_type)

        if not parser:
            return False, f"不支持的文件类型: {file_path.name}", None

        return parser.parse(file_path)
