"""
技能理解系统
帮助 Agent 理解技能的能力、使用场景和调用方式
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class SkillUnderstanding:
    """技能理解器"""

    def __init__(self, config):
        self.config = config
        self.understanding_path = Path(config.get('system.understanding_path',
                                                   config.get('system.registry_path').replace('skills_registry', 'skills_understanding')))

    def generate_understanding(self, skill_data: Dict) -> Dict:
        """
        为技能生成理解信息

        Returns:
            技能理解信息，包含：
            - capabilities: 能力列表
            - usage_patterns: 使用模式
            - invocation_methods: 调用方式
            - examples: 使用示例
            - when_to_use: 何时使用
        """
        skill_type = skill_data.get('skill_type', 'unknown')

        if skill_type == 'claude_md':
            return self._understand_claude_md(skill_data)
        elif skill_type == 'agent_md':
            return self._understand_agent_md(skill_data)
        elif skill_type == 'skill_md':
            return self._understand_skill_md(skill_data)
        else:
            return self._understand_generic(skill_data)

    def _understand_claude_md(self, skill_data: Dict) -> Dict:
        """理解 CLAUDE.md 文件"""
        content = skill_data.get('content', '')
        project_context = skill_data.get('project_context', {})

        # 从内容中提取能力
        capabilities = self._extract_claude_md_capabilities(content, project_context)

        return {
            'skill_name': skill_data.get('name'),
            'skill_type': 'claude_md',
            'capabilities': capabilities,
            'usage_patterns': [
                '项目级决策时参考',
                '理解项目架构和约定',
                '遵循项目特定的工作流程'
            ],
            'invocation_methods': {
                'context_aware': 'Claude 会自动读取项目中的 CLAUDE.md 文件',
                'manual_reference': '可以手动查看文件内容'
            },
            'when_to_use': [
                '在处理项目相关任务时',
                '需要理解项目结构和约定时',
                '需要遵循项目特定模式时'
            ],
            'metadata': {
                'path': skill_data.get('path'),
                'has_architecture': project_context.get('has_architecture', False),
                'has_commands': project_context.get('has_commands', False),
                'has_patterns': project_context.get('has_patterns', False)
            }
        }

    def _understand_agent_md(self, skill_data: Dict) -> Dict:
        """理解 AGENT.md 文件"""
        content = skill_data.get('content', '')
        capabilities = skill_data.get('capabilities', {})
        agent_type = skill_data.get('agent_type', 'custom')

        # 生成能力描述
        capability_descriptions = []
        if capabilities.get('can_use_tools'):
            capability_descriptions.append('使用工具和 API')
        if capabilities.get('can_write_code'):
            capability_descriptions.append('编写和修改代码')
        if capabilities.get('can_run_commands'):
            capability_descriptions.append('执行终端命令')
        if capabilities.get('can_search_web'):
            capability_descriptions.append('搜索网络信息')
        if capabilities.get('autonomous'):
            capability_descriptions.append('独立工作和决策')

        return {
            'skill_name': skill_data.get('name'),
            'skill_type': 'agent_md',
            'capabilities': capability_descriptions,
            'usage_patterns': [
                '作为自主 Agent 委托任务',
                '处理复杂的多步骤工作流',
                '需要特定 Agent 能力的任务'
            ],
            'invocation_methods': {
                'agent_delegation': f'使用 Agent tool 启动 {agent_type} agent',
                'direct_reference': '参考 AGENT.md 了解 Agent 行为'
            },
            'when_to_use': [
                '需要自主 Agent 处理任务时',
                '任务需要特定 Agent 能力时',
                '需要独立完成复杂工作流时'
            ],
            'metadata': {
                'agent_type': agent_type,
                'capabilities': capabilities,
                'path': skill_data.get('path')
            }
        }

    def _understand_skill_md(self, skill_data: Dict) -> Dict:
        """理解 SKILL.md 文件"""
        content = skill_data.get('content', '')
        frontmatter = skill_data.get('frontmatter', {})
        scenarios = frontmatter.get('scenarios', [])

        # 从内容中提取关键信息
        capabilities = self._extract_skill_capabilities(content, scenarios)

        # 提取代码示例
        examples = self._extract_code_examples(content)

        return {
            'skill_name': skill_data.get('name'),
            'skill_type': 'skill_md',
            'capabilities': capabilities,
            'usage_patterns': scenarios,
            'invocation_methods': {
                'skill_command': f'/{skill_data.get("name")}',
                'examples': examples
            },
            'when_to_use': self._extract_when_to_use(content),
            'metadata': {
                'complexity': frontmatter.get('complexity', 'medium'),
                'tags': frontmatter.get('tags', []),
                'version': frontmatter.get('version', '1.0.0')
            }
        }

    def _understand_generic(self, skill_data: Dict) -> Dict:
        """理解通用技能"""
        return {
            'skill_name': skill_data.get('name'),
            'skill_type': 'unknown',
            'capabilities': [skill_data.get('description', 'Unknown skill')],
            'usage_patterns': [],
            'invocation_methods': {},
            'when_to_use': [],
            'metadata': {}
        }

    def _extract_claude_md_capabilities(self, content: str, project_context: Dict) -> List[str]:
        """从 CLAUDE.md 内容中提取能力"""
        capabilities = []

        if project_context.get('has_architecture'):
            capabilities.append('提供项目架构信息')

        if project_context.get('has_commands'):
            capabilities.append('定义项目命令和工作流')

        if project_context.get('has_patterns'):
            capabilities.append('说明代码模式和约定')

        # 从内容中提取更多信息
        content_lower = content.lower()

        if 'command' in content_lower:
            capabilities.append('提供命令参考')

        if 'pattern' in content_lower or 'convention' in content_lower:
            capabilities.append('定义开发模式')

        if 'architecture' in content_lower or 'structure' in content_lower:
            capabilities.append('说明项目结构')

        return capabilities

    def _extract_skill_capabilities(self, content: str, scenarios: List[str]) -> List[str]:
        """从 SKILL.md 内容中提取能力"""
        capabilities = []

        # 从 scenarios 中提取
        if scenarios:
            capabilities.extend(scenarios)

        # 从内容中查找标题
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('##') or line.startswith('###'):
                # 这是一个标题，可能是能力描述
                capability = line.lstrip('#').strip()
                if capability and capability.lower() not in ['usage', 'examples', 'installation']:
                    capabilities.append(capability)

        return capabilities[:10]  # 限制数量

    def _extract_code_examples(self, content: str) -> List[str]:
        """从内容中提取代码示例"""
        examples = []

        lines = content.split('\n')
        in_code_block = False
        code_block = []

        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # 代码块结束
                    if code_block:
                        examples.append('\n'.join(code_block[:5]))  # 只取前5行
                        code_block = []
                    in_code_block = False
                else:
                    in_code_block = True
            elif in_code_block:
                code_block.append(line)

        return examples[:3]  # 最多返回3个示例

    def _extract_when_to_use(self, content: str) -> List[str]:
        """从内容中提取何时使用的说明"""
        when_to_use = []

        # 查找包含 "when" 或 "use" 的标题
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            if ('when' in line_lower or 'use' in line_lower) and line.startswith('#'):
                # 找到相关章节，提取接下来的几行
                for j in range(i+1, min(i+10, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith('-') or next_line.startswith('*'):
                        when_to_use.append(next_line.lstrip('-*').strip())
                    elif next_line.startswith('#'):
                        break
                    elif next_line and not next_line.startswith('#'):
                        when_to_use.append(next_line)

                if when_to_use:
                    break

        return when_to_use[:5]

    def save_understanding(self, skill_name: str, understanding: Dict):
        """保存技能理解信息"""
        self.understanding_path.parent.mkdir(parents=True, exist_ok=True)

        # 加载现有数据
        if self.understanding_path.exists():
            with open(self.understanding_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {'version': '1.0', 'last_updated': datetime.now().isoformat(), 'skills': {}}

        # 更新数据
        data['skills'][skill_name] = understanding
        data['last_updated'] = datetime.now().isoformat()

        # 保存
        with open(self.understanding_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def get_understanding(self, skill_name: str) -> Optional[Dict]:
        """获取技能理解信息"""
        if not self.understanding_path.exists():
            return None

        with open(self.understanding_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        return data.get('skills', {}).get(skill_name)

    def search_capabilities(self, query: str) -> List[Dict]:
        """根据查询搜索相关技能"""
        if not self.understanding_path.exists():
            return []

        with open(self.understanding_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        query_lower = query.lower()
        results = []

        for skill_name, understanding in data.get('skills', {}).items():
            # 在能力描述中搜索
            capabilities = understanding.get('capabilities', [])
            for capability in capabilities:
                if query_lower in capability.lower():
                    results.append({
                        'skill_name': skill_name,
                        'capability': capability,
                        'skill_type': understanding.get('skill_type'),
                        'understanding': understanding
                    })
                    break

        return results

    def get_all_understandings(self) -> Dict:
        """获取所有技能理解信息"""
        if not self.understanding_path.exists():
            return {}

        with open(self.understanding_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        return data.get('skills', {})
