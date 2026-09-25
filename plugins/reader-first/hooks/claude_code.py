#!/usr/bin/env python3
"""送る前の試し読み（フック）の、Claude Code 用の部分。hooks.json から呼ぶ。

  claude_code.py pre   PreToolUse。下書きへの Write と、GitHub の MCP の道具での投稿本文を読む
  claude_code.py stop  Stop。記録するだけ

試し読み役は `claude -p` で呼ぶ。共通の流れは gate.py にある。
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402

HOME = '~/.claude/cold-read-gate'
INTERNAL_PREFIXES = ('<task-notification>', '<system-reminder>', 'Another Claude session sent a message',
                     '<command-name>', '<local-command', 'Caveat:', 'Stop hook feedback:')


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(b.get('text', '') for b in content if isinstance(b, dict) and b.get('type') == 'text')
    return ''


def visible_events(lines):
    """依頼者に見えていたもの（依頼者の発言とAIの本文）だけを順に返す。ツールの入出力は捨てる。"""
    ev = []
    for line in lines:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get('isMeta') or d.get('isCompactSummary') or d.get('isSidechain'):
            continue
        m = d.get('message')
        if not isinstance(m, dict):
            continue
        c = m.get('content')
        if d.get('type') == 'user':
            if isinstance(c, list) and any(isinstance(b, dict) and b.get('type') == 'tool_result' for b in c):
                continue
            t = text_of(c).strip()
            if t and not t.startswith(INTERNAL_PREFIXES):
                ev.append(('requester', t))
        elif d.get('type') == 'assistant':
            t = text_of(c).strip()
            if not t:
                continue
            if ev and ev[-1][0] == 'assistant':
                ev[-1] = ('assistant', ev[-1][1] + '\n\n' + t)
            else:
                ev.append(('assistant', t))
    return ev


def target_of(tool_name, tool_input):
    """試し読みの対象なら (経路, 読み手, 本文) を返す。経路は draft（下書き）か post（投稿）。対象外なら None。"""
    if tool_name == 'Write':
        path = tool_input.get('file_path') or ''
        if gate.is_draft_path(path):
            return 'draft', gate.draft_reader(path), tool_input.get('content') or ''
        return None
    return gate.github_post(tool_name, tool_input)


def ask(system_prompt, body):
    cmd = ['claude', '-p', '--no-session-persistence', '--tools', '',
           '--system-prompt', system_prompt, '--output-format', 'json']
    model = os.environ.get('COLD_READ_GATE_MODEL')
    if model:
        cmd += ['--model', model]
    p = subprocess.run(cmd, input=body, capture_output=True, text=True, timeout=gate.TIMEOUT_SEC,
                       env=gate.child_env())
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout)[-500:])
    return json.loads(p.stdout).get('result', '')


def deny(reason):
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                   'permissionDecisionReason': reason}}


if __name__ == '__main__':
    sys.exit(gate.main(sys.argv, sys.modules[__name__]))
