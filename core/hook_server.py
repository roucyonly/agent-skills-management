"""
Hook 服务器模块
接收 Claude Code 钩子回调，追踪技能使用情况
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import uuid

from .config import get_config
from .usage_tracker import UsageTracker


class SkillInvocation:
    """技能调用记录"""

    def __init__(self, skill_name: str, session_id: str, start_time: datetime):
        self.skill_name = skill_name
        self.session_id = session_id
        self.start_time = start_time
        self.invocation_id = str(uuid.uuid4())
        self.outcome = 'unknown'
        self.duration_ms: Optional[int] = None

    def complete(self, outcome: str):
        """标记调用完成"""
        self.outcome = outcome
        self.duration_ms = int((datetime.now() - self.start_time).total_seconds() * 1000)


class HookServer:
    """Hook 服务器 - 接收 Claude Code 钩子回调"""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.tracker = UsageTracker(self.config)

        # 活跃的技能调用 {invocation_id: SkillInvocation}
        self.active_invocations: Dict[str, SkillInvocation] = {}

        # 会话级别的技能调用记录 {session_id: SkillInvocation}
        self.session_invocations: Dict[str, SkillInvocation] = {}

        # 锁
        self._lock = threading.Lock()

    def handle_hook(self, hook_data: dict) -> dict:
        """
        处理钩子回调

        hook_data 格式 (来自 Claude Code):
        {
            "hook_name": "UserPromptExpansion" | "PreToolUse" | "PostToolUse",
            "session_id": "xxx",
            "cwd": "/path/to/cwd",
            "timestamp": "ISO8601",
            "data": { ... hook-specific data ... }
        }

        返回:
        {"status": "ok"} 或 {"status": "error", "message": "..."}
        """
        hook_name = hook_data.get('hook_name')
        session_id = hook_data.get('session_id')

        if not hook_name:
            return {"status": "error", "message": "Missing hook_name"}

        try:
            if hook_name == 'UserPromptExpansion':
                return self._handle_prompt_expansion(hook_data)
            elif hook_name == 'PreToolUse':
                return self._handle_pre_tool_use(hook_data)
            elif hook_name == 'PostToolUse':
                return self._handle_post_tool_use(hook_data)
            elif hook_name == 'SessionStart':
                return self._handle_session_start(hook_data)
            elif hook_name == 'SessionEnd':
                return self._handle_session_end(hook_data)
            else:
                return {"status": "ok"}  # 忽略未知钩子
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _handle_prompt_expansion(self, hook_data: dict) -> dict:
        """
        处理用户提示扩展 - 技能调用开始

        当用户使用 /skill-name 调用技能时触发
        """
        data = hook_data.get('data', {})
        command_name = data.get('command_name')
        expansion_type = data.get('expansion_type')

        if expansion_type != 'slash_command' or not command_name:
            return {"status": "ok"}

        session_id = hook_data.get('session_id', 'unknown')
        now = datetime.now()

        invocation = SkillInvocation(
            skill_name=command_name,
            session_id=session_id,
            start_time=now
        )

        with self._lock:
            self.active_invocations[invocation.invocation_id] = invocation
            self.session_invocations[session_id] = invocation

        return {"status": "ok"}

    def _handle_pre_tool_use(self, hook_data: dict) -> dict:
        """
        处理工具使用前 - 技能工具调用开始

        PreToolUse with matcher="Skill" 时触发
        """
        data = hook_data.get('data', {})
        tool_name = data.get('tool_name')
        tool_input = data.get('tool_input', {})

        if tool_name != 'Skill':
            return {"status": "ok"}

        skill_name = tool_input.get('skill', 'unknown')
        session_id = hook_data.get('session_id', 'unknown')
        now = datetime.now()

        invocation = SkillInvocation(
            skill_name=skill_name,
            session_id=session_id,
            start_time=now
        )

        with self._lock:
            self.active_invocations[invocation.invocation_id] = invocation
            self.session_invocations[session_id] = invocation

        return {"status": "ok"}

    def _handle_post_tool_use(self, hook_data: dict) -> dict:
        """
        处理工具使用后 - 技能工具调用完成

        PostToolUse with matcher="Skill" 时触发
        """
        data = hook_data.get('data', {})
        tool_name = data.get('tool_name')

        if tool_name != 'Skill':
            return {"status": "ok"}

        session_id = hook_data.get('session_id', 'unknown')

        with self._lock:
            invocation = self.session_invocations.get(session_id)

            if invocation:
                # 确定结果
                success = data.get('success', True)
                outcome = 'success' if success else 'failure'

                invocation.complete(outcome)

                # 记录使用
                self.tracker.log_usage(
                    skill_name=invocation.skill_name,
                    outcome=outcome,
                    duration_ms=invocation.duration_ms
                )

                # 清理
                del self.session_invocations[session_id]
                if invocation.invocation_id in self.active_invocations:
                    del self.active_invocations[invocation.invocation_id]

        return {"status": "ok"}

    def _handle_session_start(self, hook_data: dict) -> dict:
        """处理会话开始"""
        return {"status": "ok"}

    def _handle_session_end(self, hook_data: dict) -> dict:
        """处理会话结束 - 清理未完成的调用"""
        session_id = hook_data.get('session_id')

        with self._lock:
            invocation = self.session_invocations.get(session_id)

            if invocation:
                # 标记为失败（会话结束但未完成）
                invocation.complete('failure')

                self.tracker.log_usage(
                    skill_name=invocation.skill_name,
                    outcome='failure',
                    duration_ms=invocation.duration_ms
                )

                del self.session_invocations[session_id]
                if invocation.invocation_id in self.active_invocations:
                    del self.active_invocations[invocation.invocation_id]

        return {"status": "ok"}

    def get_active_invocations(self) -> list:
        """获取活跃的技能调用"""
        with self._lock:
            return [
                {
                    'skill_name': inv.skill_name,
                    'session_id': inv.session_id,
                    'start_time': inv.start_time.isoformat(),
                    'invocation_id': inv.invocation_id
                }
                for inv in self.active_invocations.values()
            ]


def create_hook_script(hook_server_path: str = None) -> str:
    """
    创建 Hook 脚本内容

    这个脚本会被 Claude Code 钩子调用，接收钩子数据并转发到 hook 服务器
    """
    if hook_server_path is None:
        config = get_config()
        hook_server_path = str(Path(__file__).parent.parent / "hooks" / "hook_receiver.py")

    script = f'''#!/usr/bin/env python3
"""
Claude Code Hook 接收器
自动生成，勿手动修改
"""

import sys
import json
import urllib.request
import urllib.error

HOOK_SERVER_URL = "http://localhost:{hook_receiver_port}/hook"

def main():
    """读取 stdin 中的钩子数据并转发"""
    try:
        # 从 stdin 读取 JSON 数据
        hook_data = json.load(sys.stdin)

        # 发送到 hook 服务器
        req = urllib.request.Request(
            HOOK_SERVER_URL,
            data=json.dumps(hook_data).encode('utf-8'),
            headers={{'Content-Type': 'application/json'}},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            response.read()

    except Exception as e:
        # 静默失败，不影响 Claude Code 正常流程
        print(f"Hook error: {{e}}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
'''

    return script


def generate_settings_json_hooks(project_path: str = None, hook_server_port: int = 18792) -> dict:
    """
    生成 Claude Code settings.json 钩子配置

    返回需要添加到 settings.json 的 hooks 部分
    """
    if project_path is None:
        # 用户主目录
        project_path = str(Path.home())

    # hook 脚本路径
    hook_script_path = str(Path(project_path) / ".claude" / "skills-management" / "hooks" / "hook_receiver.py")

    return {
        "hooks": {
            "UserPromptExpansion": [
                {
                    "matcher": ".*",  # 匹配所有技能调用
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'python "{hook_script_path}" UserPromptExpansion'
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
                            "command": f'python "{hook_script_path}" PreToolUse'
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
                            "command": f'python "{hook_script_path}" PostToolUse'
                        }
                    ]
                }
            ]
        }
    }