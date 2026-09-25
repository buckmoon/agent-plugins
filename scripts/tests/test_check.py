import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import check  # noqa: E402


def write(root, rel, data):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f)


def repo(claude_version='0.1.0', codex_version='0.1.0', market_version='0.1.0', codex_listed=True):
    root = tempfile.mkdtemp()
    write(root, '.claude-plugin/marketplace.json',
          {'name': 'm', 'plugins': [{'name': 'p', 'version': market_version, 'source': './plugins/p'}]})
    write(root, '.agents/plugins/marketplace.json',
          {'name': 'm', 'plugins': [{'name': 'p', 'source': {'source': 'local', 'path': './plugins/p'}}] if codex_listed else []})
    write(root, 'plugins/p/.claude-plugin/plugin.json', {'name': 'p', 'version': claude_version})
    write(root, 'plugins/p/.codex-plugin/plugin.json', {'name': 'p', 'version': codex_version})
    return root


class CheckTest(unittest.TestCase):
    def test_consistent_repo_has_no_problems(self):
        self.assertEqual(check.problems(repo()), [])

    def test_plugin_versions_must_match(self):
        self.assertTrue(any('0.2.0' in p for p in check.problems(repo(codex_version='0.2.0'))))

    def test_marketplace_version_must_match_plugin(self):
        self.assertTrue(any('0.0.9' in p for p in check.problems(repo(market_version='0.0.9'))))

    def test_every_plugin_is_listed_in_both_marketplaces(self):
        self.assertTrue(any('Codex' in p for p in check.problems(repo(codex_listed=False))))


if __name__ == '__main__':
    unittest.main()
