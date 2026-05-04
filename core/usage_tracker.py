"""
使用追踪器模块
追踪技能使用情况和统计信息
"""

import yaml
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

class UsageTracker:
    """使用追踪器"""

    def __init__(self, config):
        self.config = config
        self.usage_path = Path(config.get('system.usage_path'))
        self.usage_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用数据
        self.usage_data = {}

        # 加载现有数据
        self._load_usage_data()

    def _load_usage_data(self):
        """从文件加载使用数据"""
        if not self.usage_path.exists():
            # 创建空的数据结构
            self._save_usage_data()
            return

        try:
            with open(self.usage_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'skills' in data:
                    self.usage_data = data['skills']
        except Exception as e:
            print(f"WARNING  加载使用数据失败: {e}")
            self.usage_data = {}

    def _save_usage_data(self):
        """保存使用数据到文件"""
        data = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'skills': self.usage_data
        }

        with open(self.usage_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def log_usage(self, skill_name: str, outcome: str, duration_ms: int = None):
        """记录技能使用"""
        if skill_name not in self.usage_data:
            self.usage_data[skill_name] = {
                'usage_count': 0,
                'first_used': None,
                'last_used': None,
                'avg_duration_ms': 0,
                'success_count': 0,
                'failure_count': 0,
                'outcomes': [],
                'usage_by_day': {}
            }

        skill_data = self.usage_data[skill_name]
        now = datetime.now()

        # 更新基本信息
        skill_data['usage_count'] += 1
        skill_data['last_used'] = now.isoformat()

        if not skill_data['first_used']:
            skill_data['first_used'] = now.isoformat()

        # 更新结果统计
        if outcome == 'success':
            skill_data['success_count'] += 1
        else:
            skill_data['failure_count'] += 1

        # 更新平均持续时间
        if duration_ms:
            current_avg = skill_data.get('avg_duration_ms', 0)
            total_count = skill_data['usage_count']
            skill_data['avg_duration_ms'] = (
                (current_avg * (total_count - 1) + duration_ms) / total_count
            )

        # 记录结果详情
        outcome_record = {
            'timestamp': now.isoformat(),
            'outcome': outcome
        }
        if duration_ms:
            outcome_record['duration_ms'] = duration_ms

        # 只保留最近100条记录
        skill_data['outcomes'] = skill_data.get('outcomes', [])[-99:]
        skill_data['outcomes'].append(outcome_record)

        # 更新每日统计
        date_key = now.strftime('%Y-%m-%d')
        skill_data['usage_by_day'][date_key] = skill_data['usage_by_day'].get(date_key, 0) + 1

        # 保存数据
        self._save_usage_data()

    def get_stats(self, skill_name: str) -> Dict:
        """获取技能统计信息"""
        if skill_name not in self.usage_data:
            return {}

        skill_data = self.usage_data[skill_name]

        # 计算成功率
        total = skill_data['success_count'] + skill_data['failure_count']
        success_rate = skill_data['success_count'] / total if total > 0 else 0

        # 计算趋势
        trend = self._calculate_trend(skill_name)

        return {
            'name': skill_name,
            'usage_count': skill_data['usage_count'],
            'first_used': skill_data['first_used'],
            'last_used': skill_data['last_used'],
            'avg_duration_ms': skill_data.get('avg_duration_ms', 0),
            'success_rate': success_rate,
            'trend': trend
        }

    def get_top_skills(self, limit: int = 10, period_days: int = None) -> List[Dict]:
        """获取最常用的技能"""
        skills_list = []

        for skill_name, skill_data in self.usage_data.items():
            stats = self.get_stats(skill_name)

            # 如果指定了时间范围，进行过滤
            if period_days:
                cutoff = datetime.now() - timedelta(days=period_days)
                last_used = datetime.fromisoformat(stats['last_used'])
                if last_used < cutoff:
                    continue

            skills_list.append(stats)

        # 按使用次数排序
        skills_list.sort(key=lambda x: x['usage_count'], reverse=True)

        return skills_list[:limit]

    def get_unused_skills(self, days: int = 90) -> List[str]:
        """获取未使用的技能"""
        cutoff = datetime.now() - timedelta(days=days)
        unused = []

        for skill_name, skill_data in self.usage_data.items():
            if not skill_data['last_used']:
                continue

            last_used = datetime.fromisoformat(skill_data['last_used'])
            if last_used < cutoff:
                unused.append(skill_name)

        return unused

    def get_underperforming_skills(self, success_threshold: float = 0.7) -> List[Dict]:
        """获取表现不佳的技能"""
        underperforming = []

        for skill_name, skill_data in self.usage_data.items():
            stats = self.get_stats(skill_name)

            if stats['success_rate'] < success_threshold:
                underperforming.append(stats)

        return underperforming

    def _calculate_trend(self, skill_name: str) -> str:
        """计算使用趋势"""
        skill_data = self.usage_data.get(skill_name)
        if not skill_data:
            return 'unknown'

        usage_by_day = skill_data.get('usage_by_day', {})
        if not usage_by_day:
            return 'stable'

        # 获取最近7天的数据
        recent_days = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            recent_days.append(usage_by_day.get(date_key, 0))

        # 简单趋势判断
        if sum(recent_days[:3]) > sum(recent_days[4:]):
            return 'increasing'
        elif sum(recent_days[:3]) < sum(recent_days[4:]):
            return 'decreasing'
        else:
            return 'stable'

    def get_summary(self, period_days: int = 30) -> Dict:
        """获取使用摘要"""
        cutoff = datetime.now() - timedelta(days=period_days)

        total_invocations = 0
        unique_skills = 0
        success_count = 0
        failure_count = 0

        for skill_name, skill_data in self.usage_data.items():
            # 检查是否有最近的使用记录
            has_recent = False
            for outcome in skill_data.get('outcomes', []):
                outcome_time = datetime.fromisoformat(outcome['timestamp'])
                if outcome_time >= cutoff:
                    has_recent = True
                    total_invocations += 1
                    if outcome['outcome'] == 'success':
                        success_count += 1
                    else:
                        failure_count += 1

            if has_recent:
                unique_skills += 1

        success_rate = success_count / total_invocations if total_invocations > 0 else 0

        return {
            'period_days': period_days,
            'total_invocations': total_invocations,
            'unique_skills': unique_skills,
            'success_rate': success_rate,
            'success_count': success_count,
            'failure_count': failure_count
        }

    def export_report(self, period: str = 'week') -> str:
        """导出使用报告"""
        days = 7 if period == 'week' else 30

        summary = self.get_summary(days)
        top_skills = self.get_top_skills(10, days)

        report = f"""
# 技能使用报告 - {period.capitalize()}

## 总体统计

- **统计周期**: {days} 天
- **总调用次数**: {summary['total_invocations']}
- **使用技能数**: {summary['unique_skills']}
- **成功率**: {summary['success_rate']:.1%}
- **成功次数**: {summary['success_count']}
- **失败次数**: {summary['failure_count']}

## 热门技能

| 排名 | 技能名称 | 使用次数 | 成功率 | 趋势 |
|------|---------|---------|--------|------|
"""

        for i, skill in enumerate(top_skills, 1):
            trend_icon = {
                'increasing': '↗️',
                'decreasing': '↘️',
                'stable': '→'
            }.get(skill['trend'], '→')

            report += f"| {i} | {skill['name']} | {skill['usage_count']} | {skill['success_rate']:.1%} | {trend_icon} |\n"

        return report
