"""
配置管理模块
管理技能管理系统的所有配置
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = None):
        self.config_dir = Path.home() / ".claude" / "skills-management"
        self.config_file = self.config_dir / "data" / "config.yaml"

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "data" / "hot").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "data" / "warm").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "data" / "cold").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "reports" / "weekly").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "reports" / "monthly").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "reports" / "roi").mkdir(parents=True, exist_ok=True)

        # 加载配置
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_file.exists():
            # 创建默认配置
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"WARNING  加载配置失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'system': {
                'registry_path': str(self.config_dir / "data" / "hot" / "skills_registry.yaml"),
                'usage_path': str(self.config_dir / "data" / "hot" / "skills_usage.yaml"),
                'similarity_threshold': 0.7,
                'unused_threshold_days': 90,
                'underperforming_threshold': 0.7
            },

            'discovery': {
                'enabled': True,
                'scan_frequency': 'automatic',
                'scan_interval_minutes': 5,
                'scan_paths': [
                    {
                        'path': str(Path.home() / ".claude" / "plugins" / "local" / "skills"),
                        'type': 'local',
                        'recursive': True,
                        'skill_pattern': '*/SKILL.md'
                    },
                    {
                        'path': str(Path.home() / ".claude" / "node_modules"),
                        'type': 'npm_global',
                        'recursive': True,
                        'skill_pattern': '*/SKILL.md'
                    },
                    {
                        'path': './node_modules',
                        'type': 'npm_local',
                        'recursive': True,
                        'skill_pattern': '*/SKILL.md'
                    },
                    {
                        'path': './.claude/skills',
                        'type': 'project',
                        'recursive': True,
                        'skill_pattern': '*/SKILL.md'
                    }
                ],
                'ignore_paths': [
                    '**/node_modules/**/test/**',
                    '**/node_modules/**/examples/**',
                    '**/.git/**'
                ],
                'auto_register': True,
                'require_validation': True,
                'enable_npm_heuristics': True,
                'npm_ignore_patterns': [
                    'react', 'vue', 'angular', 'jquery', 'lodash',
                    'express', 'koa', 'fastify',
                    'babel', 'webpack', 'vite',
                    'eslint', 'prettier', 'jest',
                    'typescript', 'ts-node'
                ],
                'notifications': {
                    'on_new_skill': True,
                    'on_skill_update': True,
                    'on_skill_removed': True
                }
            },

            'data_retention': {
                'hot_period_months': 2,
                'warm_period_months': 6,
                'compress_after_months': 6,
                'auto_archive': True,
                'archive_check_frequency': 'daily',
                'delete_after_years': None
            },

            'roi': {
                'enabled': True,
                'hourly_rate': 50,
                'baseline_period_days': 14,
                'measurement_period_days': 30,
                'auto_track_time': True,
                'development_cost_amortization_months': 12,
                'benefit_weights': {
                    'time_saved': 1.0,
                    'success_rate_improvement': 1.5,
                    'discovery_improvement': 0.8,
                    'quality_improvement': 1.2
                },
                'roi_report_frequency': 'monthly',
                'include_projections': True,
                'projection_months': 12
            },

            'cleanup': {
                'auto_archive': True,
                'archive_path': str(self.config_dir / "archive"),
                'backup_before_removal': True
            },

            'reporting': {
                'output_path': str(self.config_dir / "reports"),
                'weekly_report_day': 'sunday',
                'monthly_cleanup_day': 1,
                'include_charts': True,
                'include_roi_metrics': True
            },

            'similarity': {
                'cache_enabled': True,
                'cache_duration_hours': 168,
                'weights': {
                    'name': 0.3,
                    'description': 0.4,
                    'tags': 0.2,
                    'content': 0.1
                }
            },

            'performance': {
                'preload_archives': False,
                'cache_warm_queries': True,
                'max_memory_mb': 10
            }
        }

    def _save_config(self, config: Dict[str, Any]):
        """保存配置到文件"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config(self.config)

    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()


# 全局配置实例
_config_instance = None

def get_config() -> ConfigManager:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
