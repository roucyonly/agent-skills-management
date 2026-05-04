#!/usr/bin/env python3
"""
Claude Code Skill Hook 接收器
由 skills-management 自动生成

每次技能被使用时由 Claude Code 钩子调用，直接记录使用情况到文件
无需后台进程

接收来自 Claude Code 钩子的回调参数:
- argv[1]: hook 名称 (UserPromptExpansion/PreToolUse/PostToolUse)
- argv[2]: 会话ID (可选)
- stdin: JSON 格式的钩子数据
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.usage_tracker import UsageTracker
from core.config import get_config


class SimpleHookRecorder:
    """简单的 Hook 记录器 - 直接写入文件"""

    def __init__(self):
        self.config = get_config()
        self.tracker = UsageTracker(self.config)
        # 内存缓存当前会话的技能调用
        self._session_cache = {}

    def record_invocation_start(self, skill_name: str, session_id: str):
        """记录技能调用开始"""
        self._session_cache[session_id] = {
            'skill_name': skill_name,
            'start_time': datetime.now()
        }

    def record_invocation_end(self, skill_name: str, session_id: str, outcome: str):
        """记录技能调用结束"""
        session_data = self._session_cache.pop(session_id, None)

        if session_data:
            start_time = session_data['start_time']
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            self.tracker.log_usage(
                skill_name=skill_name,
                outcome=outcome,
                duration_ms=duration_ms
            )
        else:
            # 兜底：没有开始记录，也记录一次
            self.tracker.log_usage(
                skill_name=skill_name,
                outcome=outcome
            )

    def handle_hook(self, hook_name: str, hook_data: dict) -> bool:
        """
        处理钩子数据

        Args:
            hook_name: 钩子名称
            hook_data: 来自 stdin 的 JSON 数据

        Returns:
            是否成功处理
        """
        try:
            if hook_name == 'UserPromptExpansion':
                return self._handle_prompt_expansion(hook_data)
            elif hook_name == 'PreToolUse':
                return self._handle_pre_tool_use(hook_data)
            elif hook_name == 'PostToolUse':
                return self._handle_post_tool_use(hook_data)
            elif hook_name == 'SessionEnd':
                return self._handle_session_end(hook_data)
            return True
        except Exception as e:
            print(f"Hook error: {e}", file=sys.stderr)
            return False

    def _handle_prompt_expansion(self, hook_data: dict) -> bool:
        """
        处理技能调用开始 (slash command)
        """
        data = hook_data.get('data', {})
        command_name = data.get('command_name')
        expansion_type = data.get('expansion_type')

        if expansion_type != 'slash_command' or not command_name:
            return True

        session_id = hook_data.get('session_id', 'default')
        self.record_invocation_start(command_name, session_id)
        return True

    def _handle_pre_tool_use(self, hook_data: dict) -> bool:
        """
        处理 Skill 工具调用开始
        """
        data = hook_data.get('data', {})
        tool_name = data.get('tool_name')

        if tool_name != 'Skill':
            return True

        tool_input = data.get('tool_input', {})
        skill_name = tool_input.get('skill', 'unknown')
        session_id = hook_data.get('session_id', 'default')

        self.record_invocation_start(skill_name, session_id)
        return True

    def _handle_post_tool_use(self, hook_data: dict) -> bool:
        """
        处理 Skill 工具调用结束
        """
        data = hook_data.get('data', {})
        tool_name = data.get('tool_name')

        if tool_name != 'Skill':
            return True

        tool_input = data.get('tool_input', {})
        skill_name = tool_input.get('skill', 'unknown')
        session_id = hook_data.get('session_id', 'default')

        success = data.get('success', True)
        outcome = 'success' if success else 'failure'

        self.record_invocation_end(skill_name, session_id, outcome)
        return True

    def _handle_session_end(self, hook_data: dict) -> bool:
        """
        处理会话结束
        """
        session_id = hook_data.get('session_id', 'default')

        # 清理未完成的会话调用
        if session_id in self._session_cache:
            del self._session_cache[session_id]

        return True


def main():
    """主入口"""
    if len(sys.argv) < 2:
        print("Usage: hook_receiver.py <hook_name> [session_id]", file=sys.stderr)
        sys.exit(0)

    hook_name = sys.argv[1]
    session_id = sys.argv[2] if len(sys.argv) > 2 else 'default'

    # 从 stdin 读取钩子数据
    try:
        hook_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Failed to parse hook data: {e}", file=sys.stderr)
        sys.exit(0)

    # 添加元数据
    hook_data['hook_name'] = hook_name
    hook_data['session_id'] = session_id
    hook_data['timestamp'] = datetime.now().isoformat()

    # 处理钩子
    recorder = SimpleHookRecorder()
    recorder.handle_hook(hook_name, hook_data)

    sys.exit(0)


if __name__ == "__main__":
    main()