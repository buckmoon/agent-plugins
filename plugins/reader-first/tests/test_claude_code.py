import io
import json
import os
import sys
import tempfile
import unittest

import helpers  # noqa: F401
import claude_code as host
import gate as g


def line(**d):
    return json.dumps(d, ensure_ascii=False)


TRANSCRIPT = [
    line(type='user', message={'role': 'user', 'content': 'READMEを直して'}),
    line(type='assistant', message={'role': 'assistant', 'content': [{'type': 'text', 'text': '直します。'},
                                                                      {'type': 'tool_use', 'id': 't1', 'name': 'Read', 'input': {}}]}),
    line(type='user', message={'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 't1', 'content': 'SECRET_INTERNAL_NAME'}]}),
    line(type='user', isMeta=True, message={'role': 'user', 'content': 'meta'}),
    line(type='user', message={'role': 'user', 'content': '<system-reminder>x</system-reminder>'}),
    line(type='assistant', message={'role': 'assistant', 'content': [{'type': 'text', 'text': '報告1'}]}),
    line(type='user', message={'role': 'user', 'content': [{'type': 'text', 'text': '次はテストも'}]}),
    line(type='assistant', message={'role': 'assistant', 'content': [{'type': 'text', 'text': '最終報告A'}]}),
    line(type='assistant', message={'role': 'assistant', 'content': [{'type': 'text', 'text': '最終報告B'}]}),
]


class VisibleEventsTest(unittest.TestCase):
    def test_drops_tool_io_meta_and_reminders(self):
        ev = host.visible_events(TRANSCRIPT)
        self.assertEqual([r for r, _ in ev], ['requester', 'assistant', 'requester', 'assistant'])
        self.assertNotIn('SECRET_INTERNAL_NAME', json.dumps(ev, ensure_ascii=False))

    def test_consecutive_assistant_texts_are_one_report(self):
        _, report = g.split_record_and_report(host.visible_events(TRANSCRIPT))
        self.assertEqual(report, '最終報告A\n\n最終報告B')


class TargetTest(unittest.TestCase):
    def test_only_draft_writes_and_github_bodies_are_targets(self):
        d = '/tmp/reader-first-drafts/'
        self.assertEqual(host.target_of('Write', {'file_path': d + 'a.md', 'content': 'x'}), ('draft', 'requester', 'x'))
        self.assertEqual(host.target_of('Write', {'file_path': 'reader-first-drafts/a.md', 'content': 'x'}), ('draft', 'requester', 'x'))
        self.assertEqual(host.target_of('Write', {'file_path': d + 'slack-1.md', 'content': 'x'}), ('draft', 'slack', 'x'))
        self.assertIsNone(host.target_of('Write', {'file_path': '/p/src/a.ts', 'content': 'x'}))
        self.assertIsNone(host.target_of('Write', {'file_path': '/p/.claude/cold-read-gate/drafts/a.md', 'content': 'x'}))
        self.assertEqual(host.target_of('mcp__github__add_issue_comment', {'body': 'b'}), ('post', 'github', 'b'))
        self.assertIsNone(host.target_of('Bash', {'command': 'ls'}))


class PreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.environ['COLD_READ_GATE_HOME'] = self.dir
        self.calls = 0

        def fake_reader(record, text, audience, h):
            self.calls += 1
            self.audience = audience
            return {'reply_clear': False, 'stuck': []}
        self.orig = g.run_reader
        g.run_reader = fake_reader

    def tearDown(self):
        g.run_reader = self.orig
        del os.environ['COLD_READ_GATE_HOME']

    def inp(self, content, name='a.md'):
        return {'session_id': 's', 'tool_name': 'Write', 'transcript_path': '/nonexistent',
                'tool_input': {'file_path': self.dir + '/reader-first-drafts/' + name, 'content': content}}

    def test_short_draft_passes_without_reading(self):
        self.assertIsNone(g.pre(self.inp('短い'), host))
        self.assertEqual(self.calls, 0)

    def test_long_draft_is_denied_once_per_turn(self):
        out = g.pre(self.inp('あ' * 500), host)
        self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.audience, 'requester')
        self.assertIsNone(g.pre(self.inp('い' * 500), host))

    def test_third_party_draft_uses_its_reader_and_its_own_block(self):
        self.assertEqual(g.pre(self.inp('あ' * 500), host)['hookSpecificOutput']['permissionDecision'], 'deny')
        out = g.pre(self.inp('う' * 500, 'slack-1.md'), host)
        self.assertEqual(self.audience, 'slack')
        self.assertEqual(out['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_reader_failure_fails_open(self):
        def boom(*a):
            raise RuntimeError('x')
        g.run_reader = boom
        self.assertIsNone(g.pre(self.inp('あ' * 500), host))


class MainGuardTest(unittest.TestCase):
    def test_child_process_does_nothing(self):
        os.environ[g.CHILD_ENV] = '1'
        try:
            sys.stdin = io.StringIO(json.dumps({'tool_name': 'Write'}))
            self.assertEqual(g.main(['x', 'pre'], host), 0)
        finally:
            del os.environ[g.CHILD_ENV]
            sys.stdin = sys.__stdin__


if __name__ == '__main__':
    unittest.main()
