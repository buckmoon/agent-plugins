"""mock-notes のスキルと部品のファイルが、そろっていて壊れていないかを確かめる。

画面の動き（リーフの位置・再生・検証など）はブラウザが要るので、ここでは確かめない。
"""
import os
import re
import shutil
import subprocess
import unittest

SKILL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'skills', 'mock-notes')


def read(name):
    with open(os.path.join(SKILL_DIR, name), encoding='utf-8') as f:
        return f.read()


class SkillFilesTest(unittest.TestCase):
    def test_frontmatter(self):
        text = read('SKILL.md')
        m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
        self.assertIsNotNone(m, 'SKILL.md の先頭に frontmatter がない')
        fields = dict(line.split(': ', 1) for line in m.group(1).splitlines() if ': ' in line)
        self.assertEqual(fields.get('name'), 'mock-notes')
        self.assertTrue(fields.get('description'))
        self.assertLessEqual(len(m.group(1)), 1024, 'frontmatter が 1024 文字を超えている')

    def test_referenced_files_exist(self):
        text = read('SKILL.md')
        for name in sorted(set(re.findall(r'`([\w.-]+\.(?:md|html|js))`', text))):
            self.assertTrue(os.path.exists(os.path.join(SKILL_DIR, name)), f'SKILL.md が挙げる {name} がない')

    def test_example_uses_library(self):
        text = read('example.html')
        self.assertIn('src="mock-notes.js"', text)
        self.assertIn('MockNotes.init(', text)
        ids = re.findall(r"\bid: '([\w-]+)', kind:", text)
        self.assertGreaterEqual(len(ids), 3)
        self.assertEqual(len(ids), len(set(ids)), '見本の注記の id が重複している')
        kinds = set(re.findall(r"kind: '(\w+)'", text))
        self.assertEqual(kinds, {'fixed', 'conflict', 'assumption'}, '見本に3種類の注記がそろっていない')

    def test_library_makes_no_network_calls(self):
        text = read('mock-notes.js')
        for word in ('fetch(', 'XMLHttpRequest', 'sendBeacon', 'WebSocket', 'import('):
            self.assertNotIn(word, text)
        urls = set(re.findall(r'https?://[^\s\'"<>)]+', text))
        self.assertEqual(urls, {'http://www.w3.org/2000/svg'}, f'外部の URL がある: {urls}')

    @unittest.skipUnless(shutil.which('node'), 'node がない')
    def test_library_syntax(self):
        r = subprocess.run(['node', '--check', os.path.join(SKILL_DIR, 'mock-notes.js')], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == '__main__':
    unittest.main()
