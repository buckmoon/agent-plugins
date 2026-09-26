import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import helpers  # noqa: F401
import codex as host
import gate as g

D = '/var/folders/x/T/grip-for-readers-drafts/'


def patch(*sections):
    return '*** Begin Patch\n' + '\n'.join(sections) + '\n*** End Patch'


def add(path, *lines):
    return f'*** Add File: {path}\n' + '\n'.join('+' + s for s in lines)


def line(kind, **payload):
    return json.dumps({'timestamp': '2026-01-01T00:00:00Z', 'type': kind, 'payload': payload}, ensure_ascii=False)


def assistant(text, phase='final_answer'):
    return line('response_item', type='message', role='assistant', phase=phase,
                content=[{'type': 'output_text', 'text': text}])


ROLLOUT = [
    line('session_meta', id='s', base_instructions={'text': 'SYSTEM_PROMPT'}),
    line('response_item', type='message', role='developer', content=[{'type': 'input_text', 'text': 'DEVELOPER'}]),
    line('response_item', type='message', role='user', content=[{'type': 'input_text', 'text': '# AGENTS.md instructions'}]),
    line('event_msg', type='user_message', message='READMEを直して', images=[]),
    line('response_item', type='message', role='user', content=[{'type': 'input_text', 'text': 'READMEを直して'}]),
    assistant('直します。', phase='commentary'),
    line('response_item', type='function_call', name='exec_command', arguments='{"cmd":"cat SECRET_FILE"}'),
    line('response_item', type='function_call_output', output='SECRET_INTERNAL_NAME'),
    line('response_item', type='reasoning', encrypted_content='xxx'),
    assistant('報告1'),
    line('event_msg', type='item_completed', item={'type': 'UserMessage', 'content': [{'type': 'text', 'text': '次はテストも'}]}),
    assistant('最終報告A', phase='commentary'),
    assistant('最終報告B'),
    'not json',
]


class TargetTest(unittest.TestCase):
    def test_new_draft_file_in_a_patch_is_the_target(self):
        p = patch(add(D + 'slack-1.md', '# 見出し', '本文'))
        self.assertEqual(host.target_of('apply_patch', {'command': p}), ('draft', 'slack', '# 見出し\n本文'))

    def test_relative_draft_path_and_other_files_in_the_same_patch(self):
        p = patch('*** Update File: src/a.py\n@@\n-x\n+y', add('grip-for-readers-drafts/20260925-1430.md', '報告'))
        self.assertEqual(host.target_of('apply_patch', {'command': p}), ('draft', 'requester', '報告'))

    def test_edits_to_existing_drafts_and_other_files_are_not_targets(self):
        self.assertIsNone(host.target_of('apply_patch', {'command': patch(f'*** Update File: {D}a.md\n@@\n-x\n+y')}))
        self.assertIsNone(host.target_of('apply_patch', {'command': patch(add('/work/src/a.md', 'x'))}))
        self.assertIsNone(host.target_of('apply_patch', {}))

    def test_patch_given_as_a_plain_string(self):
        self.assertEqual(host.target_of('apply_patch', patch(add(D + 'doc-1.md', 'x'))), ('draft', 'doc', 'x'))

    def test_github_mcp_bodies_and_shell_commands(self):
        self.assertEqual(host.target_of('mcp__github__create_pull_request', {'body': 'b'}), ('post', 'github', 'b'))
        self.assertIsNone(host.target_of('Bash', {'command': 'gh pr create --body x'}))


class VisibleEventsTest(unittest.TestCase):
    def test_keeps_only_requester_messages_and_assistant_text(self):
        ev = host.visible_events(ROLLOUT)
        self.assertEqual(ev, [('requester', 'READMEを直して'), ('assistant', '直します。\n\n報告1'),
                              ('requester', '次はテストも'), ('assistant', '最終報告A\n\n最終報告B')])
        dump = json.dumps(ev, ensure_ascii=False)
        for secret in ('SYSTEM_PROMPT', 'DEVELOPER', 'AGENTS.md', 'SECRET'):
            self.assertNotIn(secret, dump)

    def test_same_prompt_recorded_twice_counts_once(self):
        ev = host.visible_events([line('event_msg', type='user_message', message='続けて'),
                                  line('event_msg', type='item_completed',
                                       item={'type': 'UserMessage', 'content': [{'type': 'text', 'text': '続けて'}]})])
        self.assertEqual(ev, [('requester', '続けて')])


class AskTest(unittest.TestCase):
    def test_runs_codex_exec_without_session_tools_or_user_config(self):
        calls = []

        def fake_run(cmd, **kw):
            calls.append((cmd, kw))
            out = cmd[cmd.index('--output-last-message') + 1]
            with open(out, 'w') as f:
                f.write('{"reply_clear": true, "stuck": []}')
            return mock.Mock(returncode=0, stdout='', stderr='')

        with mock.patch.object(host.subprocess, 'run', fake_run), \
                mock.patch.dict(os.environ, {'GRIP_FOR_READERS_MODEL': 'm1'}):
            raw = host.ask('指示"と改行\nを含む', '# 読む文章\n\n本文')
        self.assertEqual(json.loads(raw)['reply_clear'], True)
        cmd, kw = calls[0]
        self.assertEqual(cmd[:2], ['codex', 'exec'])
        for flag in ('--ephemeral', '--ignore-user-config', '--skip-git-repo-check'):
            self.assertIn(flag, cmd)
        self.assertEqual(cmd[cmd.index('-s') + 1], 'read-only')
        self.assertEqual(cmd[cmd.index('-m') + 1], 'm1')
        instr = next(c for c in cmd if c.startswith('developer_instructions='))
        self.assertEqual(json.loads(instr.split('=', 1)[1]), '指示"と改行\nを含む')
        self.assertIn('本文', kw['input'])
        self.assertEqual(kw['env'][g.CHILD_ENV], '1')

    def test_failure_raises_so_the_gate_fails_open(self):
        with mock.patch.object(host.subprocess, 'run', return_value=mock.Mock(returncode=1, stdout='', stderr='boom')):
            with self.assertRaises(RuntimeError):
                host.ask('p', 'b')


class NamesTest(unittest.TestCase):
    def test_records_live_under_the_plugin_name(self):
        self.assertEqual(host.HOME, '~/.codex/grip-for-readers')


class OutputTest(unittest.TestCase):
    def setUp(self):
        os.environ['GRIP_FOR_READERS_HOME'] = tempfile.mkdtemp()

    def tearDown(self):
        del os.environ['GRIP_FOR_READERS_HOME']
        sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__

    def run_main(self, mode, inp):
        sys.stdin, sys.stdout = io.StringIO(json.dumps(inp)), io.StringIO()
        g.main(['codex.py', mode], host)
        return sys.stdout.getvalue()

    def test_prints_empty_json_when_nothing_to_say(self):
        self.assertEqual(json.loads(self.run_main('stop', {'session_id': 's', 'transcript_path': None})), {})
        self.assertEqual(json.loads(self.run_main('pre', {'tool_name': 'Bash', 'tool_input': {'command': 'ls'}})), {})

    def test_deny_uses_the_pre_tool_use_decision(self):
        out = host.deny('理由')
        self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(out['hookSpecificOutput']['permissionDecisionReason'], '理由')


if __name__ == '__main__':
    unittest.main()
