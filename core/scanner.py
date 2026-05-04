"""
技能扫描器
支持文件系统监控和定时扫描
"""

import os
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import fnmatch

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object
    try:
        print("WARNING: watchdog not installed, file monitoring disabled")
        print("Install: pip install watchdog")
    except:
        pass

from .validator import SkillValidator
from .parsers import ParserFactory
from .skill_understanding import SkillUnderstanding


class SkillFileChangeHandler(FileSystemEventHandler if not WATCHDOG_AVAILABLE else object):
    """文件变化处理器"""

    def __init__(self, scanner):
        self.scanner = scanner

    def on_created(self, event):
        """文件创建"""
        file_path = Path(event.src_path)
        if self._is_skill_file(file_path):
            print(f"OK 检测到新技能: {event.src_path}")
            self.scanner._process_skill_file(
                file_path,
                {'type': 'auto_detected', 'source': 'file_monitor'}
            )

    def on_modified(self, event):
        """文件修改"""
        file_path = Path(event.src_path)
        if self._is_skill_file(file_path):
            print(f"OK 技能已更新: {event.src_path}")
            self.scanner._process_skill_file(
                file_path,
                {'type': 'auto_detected', 'source': 'file_monitor'}
            )

    def on_deleted(self, event):
        """文件删除"""
        file_path = Path(event.src_path)
        if self._is_skill_file(file_path):
            print(f"OK 技能已删除: {event.src_path}")
            if hasattr(self.scanner, 'registrar'):
                self.scanner.registrar.mark_skill_missing(event.src_path)

    def on_moved(self, event):
        """文件移动"""
        src_path = Path(event.src_path)
        dest_path = Path(event.dest_path)
        src_skill = self._is_skill_file(src_path)
        dest_skill = self._is_skill_file(dest_path)

        if src_skill or dest_skill:
            print(f"OK 技能已移动: {event.src_path} -> {event.dest_path}")
            if hasattr(self.scanner, 'registrar'):
                self.scanner.registrar.update_skill_path(event.src_path, event.dest_path)

    def _is_skill_file(self, file_path: Path) -> bool:
        """检查文件是否是技能文件"""
        skill_files = ['SKILL.md', 'skill.md', 'CLAUDE.md', 'claude.md', 'AGENT.md', 'agent.md', 'package.json']
        return file_path.name in skill_files


class SkillScanner:
    """技能扫描引擎"""

    def __init__(self, config, registrar):
        self.config = config
        self.registrar = registrar
        self.validator = SkillValidator(config)
        self.parser_factory = ParserFactory(config)
        self.understanding = SkillUnderstanding(config)
        self.scan_cache = {}
        self.observer = None

    def start_monitoring(self):
        """启动实时文件监控"""
        if not WATCHDOG_AVAILABLE:
            print("ERROR 文件监控需要 watchdog 库")
            print("   安装: pip install watchdog")
            return False

        if self.config.get('discovery.scan_frequency') != 'automatic':
            print("WARNING  文件监控未启用（配置为非自动模式）")
            return False

        event_handler = SkillFileChangeHandler(self)
        self.observer = Observer()

        # 监控所有配置的路径
        scan_paths = self.config.get('discovery.scan_paths', [])
        for scan_config in scan_paths:
            path = Path(scan_config['path']).expanduser()
            if path.exists():
                self.observer.schedule(
                    event_handler,
                    str(path),
                    recursive=scan_config.get('recursive', True)
                )
                print(f"OK Monitoring path: {path}")

        if self.observer.emitters:
            self.observer.start()
            print("OK File monitoring started")
            return True
        else:
            print("WARNING  没有可监控的路径")
            return False

    def stop_monitoring(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("OK File monitoring stopped")

    def scan_all(self, verbose: bool = False) -> Dict:
        """扫描所有配置的路径"""
        results = {
            'scanned': 0,
            'found': 0,
            'registered': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        scan_paths = self.config.get('discovery.scan_paths', [])

        if not scan_paths:
            if verbose:
                print("WARNING  没有配置扫描路径")

        for scan_config in scan_paths:
            try:
                if verbose:
                    print(f"扫描: {scan_config['path']}")

                path_results = self._scan_path(scan_config, verbose)
                results['scanned'] += path_results['scanned']
                results['found'] += path_results['found']
                results['registered'] += path_results['registered']
                results['updated'] += path_results['updated']
                results['skipped'] += path_results['skipped']
                results['errors'].extend(path_results['errors'])
            except Exception as e:
                results['errors'].append({
                    'path': scan_config['path'],
                    'error': str(e)
                })

        return results

    def _scan_path(self, scan_config: Dict, verbose: bool = False) -> Dict:
        """扫描单个路径"""
        results = {
            'scanned': 0,
            'found': 0,
            'registered': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        path = Path(scan_config['path']).expanduser()

        # 处理相对路径
        if not path.is_absolute():
            # 如果是相对路径，从当前工作目录解析
            path = Path.cwd() / scan_config['path']

        if not path.exists():
            if verbose:
                print(f"  WARNING  路径不存在: {path}")
            return results

        # 支持多个 skill_patterns
        skill_patterns = scan_config.get('skill_patterns', [scan_config.get('skill_pattern', '**/SKILL.md')])

        # 收集所有匹配的文件
        skill_files = []
        for pattern in skill_patterns:
            matched_files = list(path.glob(pattern))
            skill_files.extend(matched_files)

        # 去重
        skill_files = list(set(skill_files))

        # 应用忽略规则
        ignore_patterns = self.config.get('discovery.ignore_paths', [])
        skill_files = self._apply_ignore_rules(skill_files, ignore_patterns)

        results['scanned'] = len(skill_files)

        if verbose and skill_files:
            print(f"  发现 {len(skill_files)} 个技能文件")

        for skill_file in skill_files:
            try:
                result = self._process_skill_file(skill_file, scan_config, verbose)
                if result['action'] == 'registered':
                    results['registered'] += 1
                    results['found'] += 1
                elif result['action'] == 'updated':
                    results['updated'] += 1
                    results['found'] += 1
                elif result['action'] == 'skipped':
                    results['skipped'] += 1
            except Exception as e:
                results['errors'].append({
                    'file': str(skill_file),
                    'error': str(e)
                })

        return results

    def _process_skill_file(self, skill_file: Path, scan_config: Dict = None, verbose: bool = False) -> Dict:
        """处理单个技能文件"""
        # 使用解析器工厂解析文件
        is_valid, error_msg, skill_data = self.parser_factory.parse_file(skill_file)

        if not is_valid:
            if verbose:
                print(f"  X Invalid: {skill_file.name} - {error_msg}")
            return {'action': 'skipped', 'reason': f'invalid: {error_msg}'}

        # 计算文件哈希
        file_hash = self._calculate_hash(skill_file)
        skill_data['file_hash'] = file_hash
        skill_data['last_scanned'] = datetime.now().isoformat()

        # 检查是否已存在
        existing_skill = self.registrar.get_skill_by_path(skill_file)

        if existing_skill:
            # 检查是否有更新
            if existing_skill.get('file_hash') != file_hash:
                # 技能已更新
                if scan_config:
                    skill_data['source_type'] = scan_config.get('type', 'unknown')
                    skill_data['source_path'] = scan_config.get('path', '')

                self.registrar.update_skill(existing_skill['name'], skill_data)

                if verbose:
                    print(f"  OK Updated: {skill_data['name']}")

                return {'action': 'updated', 'skill': skill_data}
            else:
                return {'action': 'skipped', 'reason': 'unchanged'}
        else:
            # 新技能
            if scan_config:
                skill_data['source_type'] = scan_config.get('type', 'unknown')
                skill_data['source_path'] = scan_config.get('path', '')

            # 自动注册
            if self.config.get('discovery.auto_register', True):
                self.registrar.add_skill_from_discovery(skill_data)

                # 生成技能理解信息
                try:
                    understanding = self.understanding.generate_understanding(skill_data)
                    self.understanding.save_understanding(skill_data['name'], understanding)
                except Exception as e:
                    if verbose:
                        print(f"  WARNING  Failed to generate understanding: {e}")

                if verbose:
                    print(f"  OK Registered: {skill_data['name']}")

                return {'action': 'registered', 'skill': skill_data}
            else:
                return {'action': 'skipped', 'reason': 'auto_register disabled'}

        return {'action': 'skipped', 'reason': 'unknown'}

    def _extract_skill_data(self, skill_file: Path) -> Optional[Dict]:
        """从技能文件提取数据（使用解析器）"""
        try:
            is_valid, error_msg, skill_data = self.parser_factory.parse_file(skill_file)
            if is_valid:
                return skill_data
        except Exception as e:
            print(f"ERROR 解析技能失败 ({skill_file}): {e}")
        return None

    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
            return hasher.hexdigest()
        except Exception:
            return ''

    def _apply_ignore_rules(self, files: List[Path], ignore_patterns: List[str]) -> List[Path]:
        """应用忽略规则"""
        filtered = []
        for file_path in files:
            ignored = False
            for pattern in ignore_patterns:
                if fnmatch.fnmatch(str(file_path), pattern):
                    ignored = True
                    break
            if not ignored:
                filtered.append(file_path)

        return filtered

    def get_status(self) -> Dict:
        """获取扫描状态"""
        scan_paths = self.config.get('discovery.scan_paths', [])

        status = {
            'monitoring_running': self.observer and self.observer.is_alive(),
            'configured_paths': [],
            'available_paths': [],
            'unavailable_paths': []
        }

        for scan_config in scan_paths:
            path = Path(scan_config['path']).expanduser()
            path_info = {
                'path': str(path),
                'type': scan_config.get('type', 'unknown'),
                'exists': path.exists(),
                'recursive': scan_config.get('recursive', False)
            }
            status['configured_paths'].append(path_info)

            if path.exists():
                status['available_paths'].append(path_info)
            else:
                status['unavailable_paths'].append(path_info)

        return status
