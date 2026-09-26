#!/usr/bin/env python3
"""送る前の試し読み（フック）の、Codex 用の部分。codex-hooks.json から呼ぶ。

  codex.py pre   PreToolUse。apply_patch で下書きを新しく作るときと、GitHub の MCP の道具での投稿本文を読む
  codex.py stop  Stop。記録するだけ

Codex はファイルの書き込みを apply_patch の差分として渡す。下書きの全文が分かるのは
新しいファイルを作るとき（Add File）だけなので、既存の下書きの書き換えは読まない。
試し読み役は `codex exec` で呼ぶ。共通の流れは gate.py にある。
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate  # noqa: E402

HOME = '~/.codex/grip-for-readers'
NOTHING = {}  # Codex のフックは、何もしないときも JSON を返す
ADD_FILE = '*** Add File: '
READER_TASK = '標準入力で渡した文章を、指示どおりに試し読みしてください。道具は使わないでください。'


def added_files(patch):
    """差分から、新しく作るファイルの (パス, 全文) を順に返す。"""
    path, lines = None, []
    for row in patch.splitlines():
        if row.startswith('*** '):
            if path is not None:
                yield path, '\n'.join(lines)
            path, lines = (row[len(ADD_FILE):].strip(), []) if row.startswith(ADD_FILE) else (None, [])
        elif path is not None and row.startswith('+'):
            lines.append(row[1:])
    if path is not None:
        yield path, '\n'.join(lines)


def target_of(tool_name, tool_input):
    """試し読みの対象なら (経路, 読み手, 本文) を返す。経路は draft（下書き）か post（投稿）。対象外なら None。"""
    if tool_name == 'apply_patch':
        patch = tool_input if isinstance(tool_input, str) else (tool_input or {}).get('command') or ''
        for path, content in added_files(patch):
            if gate.is_draft_path(path):
                return 'draft', gate.draft_reader(path), content
        return None
    return gate.github_post(tool_name, tool_input)


def requester_text(d):
    p = d.get('payload') or {}
    if d.get('type') != 'event_msg':
        return None
    if p.get('type') == 'user_message':  # コマンド行の Codex
        return p.get('message') or ''
    item = p.get('item') or {}
    if p.get('type') == 'item_completed' and item.get('type') == 'UserMessage':  # デスクトップ版の Codex
        return '\n'.join(c.get('text', '') for c in item.get('content') or [] if isinstance(c, dict))
    return None


def assistant_text(d):
    p = d.get('payload') or {}
    if d.get('type') == 'response_item' and p.get('type') == 'message' and p.get('role') == 'assistant':
        return '\n'.join(c.get('text', '') for c in p.get('content') or []
                         if isinstance(c, dict) and c.get('type') == 'output_text')
    return None


def visible_events(lines):
    """依頼者に見えていたもの（依頼者の発言とAIの本文）だけを順に返す。
    指示の差し込み（AGENTS.md など）、道具の入出力、推論は捨てる。"""
    ev = []
    for line in lines:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        t = requester_text(d)
        if t is not None:
            t = t.strip()
            if t and ev[-1:] != [('requester', t)]:
                ev.append(('requester', t))
            continue
        t = (assistant_text(d) or '').strip()
        if not t:
            continue
        if ev and ev[-1][0] == 'assistant':
            ev[-1] = ('assistant', ev[-1][1] + '\n\n' + t)
        else:
            ev.append(('assistant', t))
    return ev


def ask(system_prompt, body):
    with tempfile.TemporaryDirectory() as work:
        out = os.path.join(work, 'answer.txt')
        cmd = ['codex', 'exec', '--ephemeral', '--ignore-user-config', '--skip-git-repo-check',
               '-s', 'read-only', '-C', work,
               '-c', 'developer_instructions=' + json.dumps(system_prompt, ensure_ascii=False),
               '--output-last-message', out]
        model = os.environ.get('GRIP_FOR_READERS_MODEL')
        if model:
            cmd += ['-m', model]
        cmd.append(READER_TASK)
        p = subprocess.run(cmd, input=body, capture_output=True, text=True, timeout=gate.TIMEOUT_SEC,
                           env=gate.child_env())
        if p.returncode != 0:
            raise RuntimeError((p.stderr or p.stdout)[-500:])
        with open(out) as f:
            return f.read()


def deny(reason):
    return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                   'permissionDecisionReason': reason}}


if __name__ == '__main__':
    sys.exit(gate.main(sys.argv, sys.modules[__name__]))
