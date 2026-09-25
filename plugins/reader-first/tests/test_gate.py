import json
import os
import tempfile
import unittest

import helpers  # noqa: F401
import gate as g


class FakeHost:
    HOME = '~/.never-used'


class RecordTest(unittest.TestCase):
    EV = [('requester', 'READMEを直して'), ('assistant', '報告1'), ('requester', '次はテストも'),
          ('assistant', '最終報告A\n\n最終報告B')]

    def test_report_is_text_after_last_requester_message(self):
        record, report = g.split_record_and_report(self.EV)
        self.assertEqual(report, '最終報告A\n\n最終報告B')
        self.assertIn('次はテストも', record)
        self.assertNotIn('最終報告A', record)

    def test_last_assistant_message_wins_when_transcript_lags(self):
        _, report = g.split_record_and_report(self.EV[:3], '最終報告A\n\n最終報告B（完全版）')
        self.assertEqual(report, '最終報告A\n\n最終報告B（完全版）')

    def test_only_requester_gets_the_record(self):
        self.assertIn('これまでのやり取り', g.reader_body('記録', '本文', 'requester'))
        self.assertNotIn('記録', g.reader_body('記録', '本文', 'slack'))


class VerdictTest(unittest.TestCase):
    def test_parses_fenced_json(self):
        v = g.parse_reader_output('```json\n{"reply_clear": true, "expected_reply": "続けて", "stuck": []}\n```')
        self.assertTrue(v['reply_clear'])

    def test_block_only_when_unclear_or_stuck(self):
        self.assertFalse(g.should_block({'reply_clear': True, 'stuck': []}))
        self.assertTrue(g.should_block({'reply_clear': False, 'stuck': []}))
        self.assertTrue(g.should_block({'reply_clear': True, 'stuck': [{'quote': 'a', 'question': 'b'}]}))

    def test_reason_lists_questions(self):
        r = g.block_reason({'reply_clear': False, 'stuck': [{'quote': '案A', 'question': '案Aとは？'}]}, 'draft', 'requester')
        self.assertIn('案Aとは？', r)
        self.assertIn('何をすればよいか', r)
        self.assertIn('drafts', r)
        self.assertIn('reader-first', r)
        self.assertIn('チャット', r)
        self.assertIn('もう一度投稿', g.block_reason({'reply_clear': True, 'stuck': []}, 'post', 'github'))

    def test_reason_for_third_party_draft_names_the_prefix(self):
        r = g.block_reason({'reply_clear': True, 'stuck': []}, 'draft', 'slack')
        self.assertIn('slack-', r)
        self.assertNotIn('チャットに出して', r)

    def test_slack_reader_is_not_only_the_team(self):
        prompt = g.reader_prompt('slack')
        self.assertIn('プロジェクトの関係者', prompt)
        self.assertIn('社外の顧客', prompt)
        self.assertNotIn('読み手は、依頼者のチームのメンバーです', prompt)

    def test_every_reader_has_a_prompt(self):
        for reader in ('requester', 'github', 'slack', 'email', 'doc'):
            self.assertIn('JSON', g.reader_prompt(reader))


class DraftPathTest(unittest.TestCase):
    def test_filename_prefix_names_the_reader(self):
        for name, reader in [('slack-20260925-1800.md', 'slack'), ('email-1.md', 'email'), ('github-1.md', 'github'),
                             ('doc-1.md', 'doc'), ('requester-1.md', 'requester'), ('20260925-1800.md', 'requester'),
                             ('memo-1.md', 'requester')]:
            self.assertEqual(g.draft_reader('/d/' + name), reader, name)

    def test_drafts_live_in_reader_first_drafts_anywhere(self):
        self.assertTrue(g.is_draft_path('/var/folders/x/T/reader-first-drafts/a.md'))
        self.assertTrue(g.is_draft_path('/tmp/reader-first-drafts/slack-1.md'))
        self.assertTrue(g.is_draft_path('reader-first-drafts/a.md'))
        self.assertTrue(g.is_draft_path('C:\\Temp\\reader-first-drafts\\a.md'))
        self.assertFalse(g.is_draft_path('/home/u/src/a.md'))
        self.assertFalse(g.is_draft_path('/home/u/reader-first-drafts-old/a.md'))
        self.assertFalse(g.is_draft_path(None))


class DraftedTest(unittest.TestCase):
    def setUp(self):
        os.environ['COLD_READ_GATE_HOME'] = tempfile.mkdtemp()

    def tearDown(self):
        del os.environ['COLD_READ_GATE_HOME']

    def test_report_matching_the_sessions_last_requester_draft_counts_as_drafted(self):
        g.remember_draft(FakeHost, 's1', '依頼者への報告')
        g.remember_draft(FakeHost, 's2', '別の会話の報告')
        self.assertTrue(g.report_was_drafted(FakeHost, 's1', '依頼者への報告'))
        self.assertFalse(g.report_was_drafted(FakeHost, 's1', '別の会話の報告'))
        self.assertFalse(g.report_was_drafted(FakeHost, 's3', '依頼者への報告'))

    def test_progress_notes_before_the_drafted_text_still_count(self):
        g.remember_draft(FakeHost, 's1', '依頼者への報告')
        self.assertTrue(g.report_was_drafted(FakeHost, 's1', 'スキルを読みます。\n\n依頼者への報告'))


class LogTest(unittest.TestCase):
    def test_entries_carry_a_readable_local_time(self):
        home = tempfile.mkdtemp()
        os.environ['COLD_READ_GATE_HOME'] = home
        try:
            g.log(FakeHost, {'ts': 0, 'mode': 'pre'})
            with open(os.path.join(home, 'log.jsonl')) as f:
                entry = json.loads(f.readline())
            self.assertRegex(entry['at'], r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')
        finally:
            del os.environ['COLD_READ_GATE_HOME']


class RememberInPreTest(unittest.TestCase):
    def setUp(self):
        os.environ['COLD_READ_GATE_HOME'] = tempfile.mkdtemp()

    def tearDown(self):
        del os.environ['COLD_READ_GATE_HOME']

    def test_requester_drafts_are_remembered_even_when_short(self):
        class Host(FakeHost):
            @staticmethod
            def target_of(name, inp):
                return ('draft', inp['reader'], inp['text'])
        g.pre({'session_id': 's', 'tool_name': 'x', 'tool_input': {'reader': 'slack', 'text': 'Slackの文面'}}, Host)
        self.assertFalse(g.report_was_drafted(Host, 's', 'Slackの文面'))
        g.pre({'session_id': 's', 'tool_name': 'x', 'tool_input': {'reader': 'requester', 'text': '短い報告'}}, Host)
        self.assertTrue(g.report_was_drafted(Host, 's', '短い報告'))


if __name__ == '__main__':
    unittest.main()
