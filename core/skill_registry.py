"""
技能注册表模块
管理所有技能的注册信息
"""

import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

class SkillRegistry:
    """技能注册表"""

    def __init__(self, config):
        self.config = config
        self.registry_path = Path(config.get('system.registry_path'))
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # 技能索引
        self.skills = {}
        self.skills_by_tag = defaultdict(list)
        self.skills_by_name = {}

        # 加载现有注册表
        self._load_registry()

    def _load_registry(self):
        """从文件加载注册表"""
        if not self.registry_path.exists():
            # 创建空的注册表
            self._save_registry()
            return

        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'skills' in data:
                    self.skills = data['skills']
                    self._rebuild_indexes()
        except Exception as e:
            print(f"WARNING: Failed to load registry: {e}")
            self.skills = {}

    def _rebuild_indexes(self):
        """重建索引"""
        self.skills_by_tag = defaultdict(list)
        self.skills_by_name = {}

        for skill_name, skill_data in self.skills.items():
            # 名称索引
            self.skills_by_name[skill_name] = skill_data

            # 标签索引
            for tag in skill_data.get('tags', []):
                self.skills_by_tag[tag].append(skill_name)

    def _save_registry(self):
        """保存注册表到文件"""
        data = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'skills': self.skills
        }

        with open(self.registry_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def add_skill(self, skill_path: str) -> bool:
        """手动添加技能到注册表"""
        path = Path(skill_path).expanduser()

        if not path.exists():
            print(f"ERROR: Skill file does not exist: {skill_path}")
            return False

        # 提取技能数据
        skill_data = self._extract_skill_data(path)

        if not skill_data:
            print(f"ERROR 无法提取技能数据: {skill_path}")
            return False

        # 添加到注册表
        return self._add_skill_data(skill_data)

    def _add_skill_data(self, skill_data: Dict) -> bool:
        """添加技能数据到注册表"""
        skill_name = skill_data['name']

        # 检查是否已存在
        if skill_name in self.skills:
            print(f"WARNING  技能 '{skill_name}' 已存在，使用 update 更新")
            return False

        # 添加技能
        skill_data['registered_at'] = datetime.now().isoformat()
        skill_data['registration_method'] = 'manual'

        self.skills[skill_name] = skill_data
        self._rebuild_indexes()
        self._save_registry()

        print(f"OK 技能 '{skill_name}' 已注册")
        return True

    def add_skill_from_discovery(self, skill_data: Dict) -> bool:
        """从自动发现添加技能"""
        # 验证技能数据
        if not self._validate_skill_data(skill_data):
            return False

        skill_name = skill_data['name']

        # 检查是否已存在
        if skill_name in self.skills:
            # 技能已存在，更新而不是添加
            return self.update_skill(skill_name, skill_data)

        # 添加到注册表
        skill_data['discovered_at'] = datetime.now().isoformat()
        skill_data['registration_method'] = 'auto_discovery'

        self.skills[skill_name] = skill_data
        self._rebuild_indexes()
        self._save_registry()

        # 通知用户
        self._notify_new_skill(skill_data)

        return True

    def remove_skill(self, skill_name: str) -> bool:
        """从注册表移除技能"""
        if skill_name not in self.skills:
            print(f"ERROR 技能 '{skill_name}' 不存在")
            return False

        del self.skills[skill_name]
        self._rebuild_indexes()
        self._save_registry()

        print(f"OK 技能 '{skill_name}' 已移除")
        return True

    def update_skill(self, skill_name: str, metadata: Dict) -> bool:
        """更新技能元数据"""
        if skill_name not in self.skills:
            print(f"ERROR 技能 '{skill_name}' 不存在")
            return False

        # 更新元数据
        self.skills[skill_name].update(metadata)
        self.skills[skill_name]['last_updated'] = datetime.now().isoformat()

        self._rebuild_indexes()
        self._save_registry()

        return True

    def get_skill(self, skill_name: str) -> Optional[Dict]:
        """获取单个技能信息"""
        return self.skills.get(skill_name)

    def get_skill_by_path(self, path: Path) -> Optional[Dict]:
        """通过路径查找技能"""
        path_str = str(path)
        for skill_name, skill_data in self.skills.items():
            if skill_data.get('path') == path_str:
                return skill_data
        return None

    def list_skills(self, filters: Dict = None) -> List[Dict]:
        """列出技能（支持过滤）"""
        skills_list = list(self.skills.values())

        if not filters:
            return skills_list

        # 应用过滤
        filtered = []
        for skill in skills_list:
            match = True

            # 标签过滤
            if 'tags' in filters:
                required_tags = set(filters['tags'])
                skill_tags = set(skill.get('tags', []))
                if not required_tags.issubset(skill_tags):
                    match = False

            # 类型过滤
            if 'type' in filters:
                if skill.get('source_type') != filters['type']:
                    match = False

            # 复杂度过滤
            if 'complexity' in filters:
                if skill.get('complexity') != filters['complexity']:
                    match = False

            if match:
                filtered.append(skill)

        return filtered

    def search_skills(self, query: str) -> List[Dict]:
        """搜索技能"""
        query_lower = query.lower()
        results = []

        for skill_name, skill_data in self.skills.items():
            # 搜索名称
            if query_lower in skill_name.lower():
                results.append(skill_data)
                continue

            # 搜索描述
            description = skill_data.get('description', '')
            if query_lower in description.lower():
                results.append(skill_data)
                continue

            # 搜索标签
            tags = skill_data.get('tags', [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(skill_data)

        return results

    def sync(self) -> int:
        """同步注册表与磁盘（返回变更数量）"""
        changes = 0

        # 检查已注册的技能是否还存在
        missing_skills = []
        for skill_name, skill_data in self.skills.items():
            skill_path = Path(skill_data.get('path', ''))
            if not skill_path.exists():
                missing_skills.append(skill_name)

        # 标记缺失的技能
        for skill_name in missing_skills:
            self.skills[skill_name]['status'] = 'missing'
            self.skills[skill_name]['missing_since'] = datetime.now().isoformat()
            changes += 1

        if changes > 0:
            self._save_registry()

        return changes

    def validate(self) -> List[str]:
        """验证注册表（返回错误列表）"""
        errors = []

        for skill_name, skill_data in self.skills.items():
            # 检查必需字段
            if 'name' not in skill_data:
                errors.append(f"技能 '{skill_name}' 缺少名称")

            if 'path' not in skill_data:
                errors.append(f"技能 '{skill_name}' 缺少路径")

            # 检查路径是否存在
            skill_path = skill_data.get('path')
            if skill_path:
                path = Path(skill_path)
                if not path.exists():
                    errors.append(f"技能 '{skill_name}' 路径不存在: {skill_path}")

        return errors

    def get_stats(self) -> Dict:
        """获取注册表统计信息"""
        total = len(self.skills)

        by_type = defaultdict(int)
        by_status = defaultdict(int)

        for skill_data in self.skills.values():
            source_type = skill_data.get('source_type', 'unknown')
            status = skill_data.get('status', 'active')

            by_type[source_type] += 1
            by_status[status] += 1

        return {
            'total': total,
            'by_type': dict(by_type),
            'by_status': dict(by_status),
            'tags': len(self.skills_by_tag)
        }

    def _extract_skill_data(self, skill_file: Path) -> Optional[Dict]:
        """从 SKILL.md 提取数据"""
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 分离 frontmatter 和内容
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1]
                    skill_content = parts[2]
                    try:
                        frontmatter = yaml.safe_load(frontmatter_text)
                    except:
                        frontmatter = {}
                else:
                    frontmatter = {}
                    skill_content = content
            else:
                frontmatter = {}
                skill_content = content

            # 生成技能名称
            skill_name = frontmatter.get('name')
            if not skill_name:
                skill_name = skill_file.parent.name

            return {
                'name': skill_name,
                'display_name': frontmatter.get('description', skill_name),
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
        except Exception as e:
            print(f"ERROR 提取技能数据失败: {e}")
            return None

    def _validate_skill_data(self, skill_data: Dict) -> bool:
        """验证技能数据"""
        # 必需字段
        required_fields = ['name', 'path']
        for field in required_fields:
            if field not in skill_data:
                print(f"ERROR 技能缺少必需字段: {field}")
                return False

        # 验证路径存在
        skill_path = Path(skill_data['path'])
        if not skill_path.exists():
            print(f"ERROR 技能文件不存在: {skill_data['path']}")
            return False

        return True

    def _notify_new_skill(self, skill_data: Dict):
        """通知用户新技能"""
        if not self.config.get('discovery.notifications.on_new_skill', True):
            return

        print(f"""
============================================================
  OK New Skill Discovered
============================================================

Name: {skill_data['name']}
Description: {skill_data.get('description', 'N/A')}
Path: {skill_data['path']}
Source: {skill_data.get('source_type', 'unknown')}

Automatically registered to skills management system

Use 'skills info {skill_data['name']}' for details
""")

    def mark_skill_missing(self, path: str):
        """标记技能为缺失"""
        skill = self.get_skill_by_path(Path(path))
        if skill:
            skill['status'] = 'missing'
            skill['missing_since'] = datetime.now().isoformat()
            self._save_registry()
            print(f"WARNING  技能 '{skill['name']}' 标记为缺失")

    def update_skill_path(self, old_path: str, new_path: str):
        """更新技能路径"""
        skill = self.get_skill_by_path(Path(old_path))
        if skill:
            skill['path'] = new_path
            skill['last_updated'] = datetime.now().isoformat()
            self._save_registry()
