#!/usr/bin/env python3
"""目録（Claude Code 用と Codex 用）とプラグイン情報の、名前と版がそろっているかを確かめる。

  python3 scripts/check.py        そろっていれば何も出さずに 0 で終わる。ずれていれば一覧を出して 1 で終わる
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE_MARKET = '.claude-plugin/marketplace.json'
CODEX_MARKET = '.agents/plugins/marketplace.json'


def load(root, rel):
    with open(os.path.join(root, rel)) as f:
        return json.load(f)


def codex_path(entry):
    source = entry.get('source')
    return source.get('path') if isinstance(source, dict) else source


def problems(root):
    out = []
    claude = {p['name']: p for p in load(root, CLAUDE_MARKET)['plugins']}
    codex = {p['name']: p for p in load(root, CODEX_MARKET)['plugins']}
    for name in sorted(set(claude) - set(codex)):
        out.append(f'{name}: Codex 用の目録（{CODEX_MARKET}）にない')
    for name in sorted(set(codex) - set(claude)):
        out.append(f'{name}: Claude Code 用の目録（{CLAUDE_MARKET}）にない')
    for name in sorted(set(claude) & set(codex)):
        entry = claude[name]
        if os.path.normpath(entry['source']) != os.path.normpath(codex_path(codex[name]) or ''):
            out.append(f'{name}: 二つの目録で置き場所が違う')
        base = entry['source']
        versions = {
            CLAUDE_MARKET: entry.get('version'),
            f'{base}/.claude-plugin/plugin.json': load(root, os.path.join(base, '.claude-plugin/plugin.json')).get('version'),
            f'{base}/.codex-plugin/plugin.json': load(root, os.path.join(base, '.codex-plugin/plugin.json')).get('version'),
        }
        if len(set(versions.values())) > 1:
            listed = '、'.join(f'{k}={v}' for k, v in versions.items())
            out.append(f'{name}: 版がそろっていない（{listed}）')
    return out


if __name__ == '__main__':
    found = problems(ROOT)
    for p in found:
        print(p)
    sys.exit(1 if found else 0)
