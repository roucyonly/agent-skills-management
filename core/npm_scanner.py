"""
NPM 技能扫描器
处理通过 npm 安装的技能（带验证）
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

from .validator import SkillValidator


class NPMSkillScanner:
    """NPM 技能扫描器"""

    def __init__(self, config):
        self.npm_available = self._check_npm_available()
        self.validator = SkillValidator(config)
        self.config = config

    def _check_npm_available(self) -> bool:
        """检查 npm 是否可用"""
        try:
            result = subprocess.run(
                ['npm', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def scan_global_packages(self) -> List[Dict]:
        """扫描全局安装的 npm 包"""
        if not self.npm_available:
            print("WARNING  npm 不可用")
            return []

        try:
            result = subprocess.run(
                'npm list -g --depth=0 --json',
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )

            if result.returncode != 0:
                return []

            packages = json.loads(result.stdout)
            return self._find_skills_in_packages(packages, is_global=True)

        except subprocess.TimeoutExpired:
            print("WARNING  npm 命令超时")
            return []
        except Exception as e:
            print(f"ERROR 扫描全局 npm 包失败: {e}")
            return []

    def scan_local_packages(self, project_path: Path = None) -> List[Dict]:
        """扫描项目本地安装的 npm 包"""
        if not self.npm_available:
            return []

        if project_path is None:
            project_path = Path.cwd()

        try:
            result = subprocess.run(
                'npm list --depth=0 --json',
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )

            if result.returncode != 0:
                return []

            packages = json.loads(result.stdout)
            return self._find_skills_in_packages(packages, is_global=False, project_path=project_path)

        except subprocess.TimeoutExpired:
            print("WARNING  npm 命令超时")
            return []
        except Exception as e:
            print(f"ERROR 扫描本地 npm 包失败: {e}")
            return []

    def _find_skills_in_packages(self, packages: Dict, is_global: bool = False, project_path: Path = None) -> List[Dict]:
        """在 npm 包中查找技能（带验证）"""
        skills = []

        if 'dependencies' not in packages:
            return skills

        for package_name, package_info in packages['dependencies'].items():
            # 检查包是否包含 SKILL.md
            skill_path = self._find_skill_in_package(package_name, is_global, project_path)

            if skill_path:
                # 验证是否是真正的技能
                if self.validator.is_npm_package_skill(package_name, skill_path):
                    is_valid, error_msg, skill_data = self.validator.validate_skill_file(skill_path)

                    if is_valid:
                        skills.append({
                            'name': skill_data['name'],
                            'package_name': package_name,
                            'path': str(skill_path),
                            'source_type': 'npm_global' if is_global else 'npm_local',
                            'version': package_info.get('version', 'unknown'),
                            'skill_data': skill_data
                        })
                    else:
                        # SKILL.md 存在但验证失败
                        pass

        return skills

    def _find_skill_in_package(self, package_name: str, is_global: bool, project_path: Path = None) -> Optional[Path]:
        """在 npm 包中查找 SKILL.md"""
        if is_global:
            # 全局安装的包
            base_path = Path.home() / 'node_modules' / package_name
        else:
            # 项目本地安装的包
            base_path = (project_path or Path.cwd()) / 'node_modules' / package_name

        # 常见的位置
        possible_paths = [
            base_path / 'SKILL.md',
            base_path / 'skills' / 'SKILL.md',
            base_path / 'lib' / 'SKILL.md',
            base_path / 'dist' / 'SKILL.md',
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def check_npm_available(self) -> bool:
        """检查 npm 是否可用"""
        return self.npm_available
