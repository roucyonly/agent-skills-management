"""
Skills Management System - CLI 主入口
"""

import sys
import os
import json
import click
from pathlib import Path

# 添加核心模块路径
core_path = Path(__file__).parent.parent
sys.path.insert(0, str(core_path))

from core.config import get_config
from core.skill_registry import SkillRegistry
from core.usage_tracker import UsageTracker
from core.scanner import SkillScanner


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Skills Management System - 技能管理系统"""
    pass


@cli.command()
def sync():
    """同步技能注册表"""
    config = get_config()
    registry = SkillRegistry(config)

    changes = registry.sync()

    if changes > 0:
        click.echo(f"✓ 同步完成，发现 {changes} 个变更")
    else:
        click.echo("✓ 同步完成，注册表已是最新")


@cli.command()
@click.option('--filter-tag', help='按标签过滤')
@click.option('--filter-type', help='按类型过滤')
def list(filter_tag, filter_type):
    """列出所有技能"""
    config = get_config()
    registry = SkillRegistry(config)

    filters = {}
    if filter_tag:
        filters['tags'] = [filter_tag]
    if filter_type:
        filters['type'] = filter_type

    skills = registry.list_skills(filters)

    if not skills:
        click.echo("没有找到技能")
        return

    click.echo(f"\n找到 {len(skills)} 个技能:\n")

    for skill in skills:
        status = skill.get('status')
        if status == 'missing':
            status_icon = 'X'
        else:
            status_icon = 'OK'

        tags = ', '.join(skill.get('tags', [])[:3])
        source = skill.get('source_type', 'unknown')

        click.echo(f"{status_icon} {skill['name']}")
        click.echo(f"   Description: {skill.get('description', 'N/A')}")
        click.echo(f"   Tags: {tags}")
        click.echo(f"   Source: {source}")
        click.echo()


@cli.command()
@click.argument('skill_name')
def info(skill_name):
    """查看技能详情"""
    config = get_config()
    registry = SkillRegistry(config)
    tracker = UsageTracker(config)

    skill = registry.get_skill(skill_name)

    if not skill:
        click.echo(f"❌ 技能 '{skill_name}' 不存在")
        return

    stats = tracker.get_stats(skill_name)

    click.echo(f"\n技能: {skill_name}")
    click.echo(f"描述: {skill.get('description', 'N/A')}")
    click.echo(f"路径: {skill.get('path', 'N/A')}")

    if stats:
        click.echo(f"\n使用统计:")
        click.echo(f"  使用次数: {stats['usage_count']}")
        click.echo(f"  成功率: {stats['success_rate']:.1%}")
        click.echo(f"  首次使用: {stats.get('first_used', 'N/A')}")
        click.echo(f"  最后使用: {stats.get('last_used', 'N/A')}")

        trend_icon = {
            'increasing': '↗️',
            'decreasing': '↘️',
            'stable': '→'
        }.get(stats.get('trend', 'stable'), '→')

        click.echo(f"  趋势: {trend_icon}")

    tags = skill.get('tags', [])
    if tags:
        click.echo(f"\n标签: {', '.join(tags)}")


@cli.command()
@click.argument('query')
def search(query):
    """搜索技能"""
    config = get_config()
    registry = SkillRegistry(config)

    results = registry.search_skills(query)

    if not results:
        click.echo(f"没有找到匹配 '{query}' 的技能")
        return

    click.echo(f"\n找到 {len(results)} 个匹配的技能:\n")

    for skill in results:
        tags = ', '.join(skill.get('tags', [])[:3])
        click.echo(f"• {skill['name']}")
        click.echo(f"  {skill.get('description', 'N/A')}")
        if tags:
            click.echo(f"  标签: {tags}")
        click.echo()


@cli.command()
@click.argument('skill_path')
def add(skill_path):
    """手动添加技能"""
    config = get_config()
    registry = SkillRegistry(config)

    success = registry.add_skill(skill_path)

    if success:
        click.echo(f"✓ 技能已添加")
    else:
        click.echo("✗ 添加失败")


@cli.command()
@click.argument('skill_name')
@click.confirmation_option(prompt='确认删除技能?')
def remove(skill_name):
    """删除技能"""
    config = get_config()
    registry = SkillRegistry(config)

    success = registry.remove_skill(skill_name)

    if success:
        click.echo(f"✓ 技能 '{skill_name}' 已删除")
    else:
        click.echo(f"✗ 删除失败")


@cli.command()
@click.option('--period', default='30', help='统计周期（天数）')
@click.option('--top', default='10', help='显示热门技能数量')
def stats(period, top):
    """查看使用统计"""
    config = get_config()
    tracker = UsageTracker(config)

    period_days = int(period)

    # 总体统计
    summary = tracker.get_summary(period_days)

    click.echo(f"""
## 技能使用统计（最近 {period_days} 天）

总体统计:
  总调用次数: {summary['total_invocations']}
  使用技能数: {summary['unique_skills']}
  成功率: {summary['success_rate']:.1%}
""")

    # 热门技能
    top_skills = tracker.get_top_skills(int(top), period_days)

    if top_skills:
        click.echo(f"热门技能 (Top {len(top_skills)}):")
        click.echo()

        for i, skill in enumerate(top_skills, 1):
            trend_icon = {
                'increasing': '↗️',
                'decreasing': '↘️',
                'stable': '→'
            }.get(skill.get('trend', 'stable'), '→')

            click.echo(f"  {i}. {skill['name']}")
            click.echo(f"     使用: {skill['usage_count']} 次 | 成功率: {skill['success_rate']:.1%} | {trend_icon}")


@cli.command()
@click.option('--verbose', is_flag=True, help='显示详细信息')
def discovery(verbose):
    """技能自动发现"""
    config = get_config()
    registry = SkillRegistry(config)
    scanner = SkillScanner(config, registry)

    if not config.get('discovery.enabled', True):
        click.echo("❌ 自动发现未启用")
        return

    click.echo("扫描技能路径...\n")

    results = scanner.scan_all(verbose=verbose)

    click.echo(f"""
扫描完成:
  扫描路径: {results['scanned']}
  发现技能: {results['found']}
  新注册: {results['registered']}
  更新: {results['updated']}
  跳过: {results['skipped']}
""")

    if results['errors']:
        click.echo("\nErrors:")
        for error in results['errors']:
            path = error.get('path', 'unknown')
            error_msg = error.get('error', 'unknown error')
            click.echo(f"  X {path}: {error_msg}")


@cli.command()
def discovery_status():
    """查看发现状态"""
    config = get_config()
    scanner = SkillScanner(config, None)

    status = scanner.get_status()

    click.echo("\n技能发现状态:\n")

    click.echo("配置的扫描路径:")
    for path_info in status['configured_paths']:
        exists_icon = "✓" if path_info['exists'] else "✗"
        click.echo(f"  {exists_icon} {path_info['path']} ({path_info['type']})")

    click.echo(f"\n监控状态: {'运行中' if status['monitoring_running'] else '未运行'}")

    # 注册表统计
    registry = SkillRegistry(config)
    stats = registry.get_stats()

    click.echo(f"\n注册表统计:")
    click.echo(f"  总技能数: {stats['total']}")
    click.echo(f"  按类型: {stats['by_type']}")
    click.echo(f"  按状态: {stats['by_type']}")


@cli.command()
@click.option('--daemon', is_flag=True, help='后台运行')
def discovery_monitor(daemon):
    """启动文件监控"""
    if daemon:
        click.echo("后台模式需要使用系统服务或 systemd")
        click.echo("请使用: skills discovery monitor (前台模式)")
        return

    config = get_config()
    registry = SkillRegistry(config)
    scanner = SkillScanner(config, registry)

    click.echo("启动文件监控...")
    click.echo("按 Ctrl+C 停止\n")

    try:
        started = scanner.start_monitoring()
        if started:
            # 保持运行
            import time
            while True:
                time.sleep(1)
        else:
            click.echo("✗ 启动失败")
    except KeyboardInterrupt:
        click.echo("\n停止监控...")
        scanner.stop_monitoring()
        click.echo("✓ 已停止")


@cli.command()
@click.argument('path', required=False)
def validate(path=None):
    """验证技能文件或注册表"""
    config = get_config()

    from core.validator import SkillValidator
    validator = SkillValidator(config)

    if path:
        # 验证单个文件
        skill_file = Path(path).expanduser()
        if not skill_file.exists():
            click.echo(f"✗ 文件不存在: {path}")
            return

        is_valid, error_msg, skill_data = validator.validate_skill_file(skill_file)

        if is_valid:
            click.echo(f"OK {path} is a valid skill file")
            click.echo(f"\nSkill Name: {skill_data['name']}")
            click.echo(f"Description: {skill_data.get('description', 'N/A')}")
            click.echo(f"Tags: {', '.join(skill_data.get('tags', []))}")
        else:
            click.echo(f"X {path} is not a valid skill file")
            click.echo(f"Reason: {error_msg}")
    else:
        # 验证整个注册表
        registry = SkillRegistry(config)
        errors = registry.validate()

        if not errors:
            click.echo("OK Registry validation passed")
        else:
            click.echo(f"X Found {len(errors)} errors:")
            for error in errors:
                click.echo(f"  - {error}")


@cli.command()
@click.option('--output', help='输出文件路径')
def report(output):
    """生成使用报告"""
    config = get_config()
    tracker = UsageTracker(config)

    report = tracker.export_report('week')

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        click.echo(f"✓ 报告已保存到: {output}")
    else:
        click.echo(report)


@cli.command()
def npm_scan():
    """扫描 npm 包并显示发现的技能"""
    config = get_config()
    from core.npm_scanner import NPMSkillScanner

    scanner = NPMSkillScanner(config)

    if not scanner.check_npm_available():
        click.echo("X npm not available")
        return

    click.echo("扫描全局 npm 包...\n")

    global_packages = scanner.scan_global_packages()

    if global_packages:
        click.echo(f"发现 {len(global_packages)} 个 npm 技能包:\n")

        for pkg in global_packages:
            click.echo(f"OK {pkg['name']}")
            click.echo(f"  包名: {pkg['package_name']}")
            click.echo(f"  版本: {pkg['version']}")
            click.echo(f"  路径: {pkg['path']}")
            click.echo()
    else:
        click.echo("没有发现 npm 技能包")

    click.echo("\n扫描本地 npm 包...\n")

    local_packages = scanner.scan_local_packages()

    if local_packages:
        click.echo(f"发现 {len(local_packages)} 个本地 npm 技能包:\n")

        for pkg in local_packages:
            click.echo(f"OK {pkg['name']}")
            click.echo(f"  包名: {pkg['package_name']}")
            click.echo(f"  版本: {pkg['version']}")
            click.echo(f"  路径: {pkg['path']}")
            click.echo()
    else:
        click.echo("没有发现本地 npm 技能包")


@cli.command()
@click.argument('skill_name')
def understand(skill_name):
    """查看技能理解信息"""
    config = get_config()
    from core.skill_understanding import SkillUnderstanding

    understanding = SkillUnderstanding(config)
    skill_understanding = understanding.get_understanding(skill_name)

    if not skill_understanding:
        click.echo(f"X 未找到技能 '{skill_name}' 的理解信息")
        click.echo(f"提示: 运行 'skills discovery' 生成理解信息")
        return

    click.echo(f"\n技能: {skill_name}")
    click.echo(f"类型: {skill_understanding.get('skill_type', 'unknown')}")

    # 能力
    capabilities = skill_understanding.get('capabilities', [])
    if capabilities:
        click.echo(f"\n能力:")
        for capability in capabilities:
            click.echo(f"  - {capability}")

    # 使用模式
    usage_patterns = skill_understanding.get('usage_patterns', [])
    if usage_patterns:
        click.echo(f"\n使用模式:")
        for pattern in usage_patterns:
            click.echo(f"  - {pattern}")

    # 调用方式
    invocation = skill_understanding.get('invocation_methods', {})
    if invocation:
        click.echo(f"\n调用方式:")
        for method, details in invocation.items():
            click.echo(f"  {method}:")
            if isinstance(details, str):
                click.echo(f"    {details}")
            elif isinstance(details, list):
                for example in details:
                    click.echo(f"    - {example}")
            elif isinstance(details, dict):
                for key, value in details.items():
                    click.echo(f"    {key}: {value}")

    # 何时使用
    when_to_use = skill_understanding.get('when_to_use', [])
    if when_to_use:
        click.echo(f"\n何时使用:")
        for item in when_to_use:
            click.echo(f"  - {item}")


@cli.command()
@click.argument('query')
def search_capabilities(query):
    """搜索技能能力"""
    config = get_config()
    from core.skill_understanding import SkillUnderstanding

    understanding = SkillUnderstanding(config)
    results = understanding.search_capabilities(query)

    if not results:
        click.echo(f"未找到匹配 '{query}' 的技能能力")
        return

    click.echo(f"\n找到 {len(results)} 个匹配的技能:\n")

    for result in results:
        click.echo(f"• {result['skill_name']}")
        click.echo(f"  能力: {result['capability']}")
        click.echo(f"  类型: {result['skill_type']}")
        click.echo()


@cli.command()
def generate_understanding():
    """为所有已注册的技能生成理解信息"""
    config = get_config()
    from core.skill_understanding import SkillUnderstanding
    from core.skill_registry import SkillRegistry

    understanding = SkillUnderstanding(config)
    registry = SkillRegistry(config)

    skills = registry.list_skills()

    if not skills:
        click.echo("没有找到已注册的技能")
        return

    click.echo(f"为 {len(skills)} 个技能生成理解信息...\n")

    success_count = 0
    error_count = 0

    for skill in skills:
        skill_name = skill.get('name')
        try:
            skill_understanding = understanding.generate_understanding(skill)
            understanding.save_understanding(skill_name, skill_understanding)
            click.echo(f"OK {skill_name}")
            success_count += 1
        except Exception as e:
            click.echo(f"X {skill_name}: {e}")
            error_count += 1

    click.echo(f"\n完成: 成功 {success_count}, 失败 {error_count}")


@cli.command()
@click.option('--port', default=18792, help='Hook 服务器端口')
def hook_setup(port):
    """设置 Claude Code 钩子以追踪技能使用"""
    import json
    import shutil
    from pathlib import Path

    config = get_config()
    skills_management_dir = Path.home() / ".claude" / "skills-management"
    hook_script_path = skills_management_dir / "hooks" / "hook_receiver.py"

    # 验证 hook 脚本存在
    if not hook_script_path.exists():
        click.echo(f"X Hook 脚本不存在: {hook_script_path}")
        click.echo("请先运行 'skills hook-server start' 或重新安装 skills-management")
        return

    # Claude Code 设置文件路径
    settings_path = Path.home() / ".claude" / "settings.json"
    settings_backup = settings_path.with_suffix('.json.bak')

    # 读取现有设置
    settings = {}
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            # 备份
            shutil.copy2(settings_path, settings_backup)
            click.echo(f"✓ 已备份设置到: {settings_backup}")
        except Exception as e:
            click.echo(f"! 读取现有设置失败: {e}")

    # 生成钩子配置
    hook_script_abs = str(hook_script_path.resolve())

    new_hooks = {
        "hooks": {
            "UserPromptExpansion": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'python "{hook_script_abs}" UserPromptExpansion'
                        }
                    ]
                }
            ],
            "PreToolUse": [
                {
                    "matcher": "Skill",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'python "{hook_script_abs}" PreToolUse'
                        }
                    ]
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Skill",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'python "{hook_script_abs}" PostToolUse'
                        }
                    ]
                }
            ]
        }
    }

    # 合并钩子配置
    if "hooks" in settings:
        # 合并而不是覆盖
        for hook_event, hook_configs in new_hooks["hooks"].items():
            if hook_event not in settings["hooks"]:
                settings["hooks"][hook_event] = hook_configs
            else:
                # 添加新的 hooks 配置
                existing_matchers = [h.get("matcher") for h in settings["hooks"].get(hook_event, [])]
                for new_config in hook_configs:
                    if new_config["matcher"] not in existing_matchers:
                        settings["hooks"][hook_event].append(new_config)
    else:
        settings.update(new_hooks)

    # 保存设置
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    click.echo(f"✓ Claude Code 钩子已配置")
    click.echo(f"  钩子脚本: {hook_script_abs}")
    click.echo(f"\n设置文件: {settings_path}")
    click.echo("\n注意: 更改钩子配置后需要重启 Claude Code")


@cli.command()
@click.option('--port', default=18792, help='Hook 服务器端口')
@click.option('--daemon', is_flag=True, help='后台运行')
def hook_server(port, daemon):
    """启动 Hook 服务器（接收技能使用回调）"""
    import socket
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse

    config = get_config()

    # 检查端口是否可用
    def is_port_available(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False

    if not is_port_available(port):
        click.echo(f"X 端口 {port} 已被占用")
        click.echo("请使用 --port 指定其他端口，或关闭已有实例")
        return

    # 导入 hook 服务器
    from core.hook_server import HookServer

    server = HookServer(config)

    class HookHandler(BaseHTTPRequestHandler):
        """HTTP 请求处理器"""

        def log_message(self, format, *args):
            # 抑制 HTTP 日志
            pass

        def do_POST(self):
            if self.path != '/hook':
                self.send_error(404)
                return

            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')

            try:
                hook_data = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400)
                return

            # 处理钩子
            result = server.handle_hook(hook_data)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))

        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            elif self.path == '/active':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                active = server.get_active_invocations()
                self.wfile.write(json.dumps(active).encode('utf-8'))
            else:
                self.send_error(404)

    def run_server():
        httpd = HTTPServer(('localhost', port), HookHandler)
        click.echo(f"✓ Hook 服务器已启动 (端口 {port})")
        click.echo(f"  健康检查: http://localhost:{port}/health")
        click.echo(f"  活跃调用: http://localhost:{port}/active")
        click.echo("\n按 Ctrl+C 停止...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.shutdown()
            click.echo("\n✓ Hook 服务器已停止")

    if daemon:
        # 后台运行
        pid = os.fork()
        if pid == 0:
            # 子进程
            run_server()
    else:
        run_server()


def main():
    """主入口函数"""
    cli()


if __name__ == '__main__':
    main()
