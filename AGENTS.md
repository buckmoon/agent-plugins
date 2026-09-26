# このリポジトリで作業するAIへ

Claude Code と Codex の両方に入るプラグインを置く、公開リポジトリである。利用者は日本語話者で、スキル・フックの指示・文書は日本語で書く。

## 両方の道具で共有する

- スキルの本文（`plugins/*/skills/`）は Claude Code と Codex で同じファイルを読む。本文には、道具の名前（Write、apply_patch、AskUserQuestion など）や片方にしかないパスを書かず、「ファイルに書く」「選択を尋ねる道具」のように一般的な言葉で書く。道具ごとに違う手順は、本文の中で道具ごとの節に分けるか、別のファイルに分ける。
- フックは、両方で同じ流れを `hooks/gate.py` に置き、道具ごとの違い（止める対象の見分け方、会話記録の読み方、試し読み役の呼び方、止め方）を `hooks/claude_code.py` と `hooks/codex.py` に置く。片方だけを直したときは、もう片方にも同じ直しが要るかを確かめる。
- フックは、失敗したら止めずに通す（fail open）。止めるのは同じ依頼の中で読み手ごとに1回だけ。理由は `docs/design.md` にある。

## 公開リポジトリとして

コミットする文章やテストに、実際の作業のやり取り、社内の issue 番号・製品名、人の名前を入れない。例が要るときは作った例を使う。

## 版を上げるとき

版は4か所にある。`.claude-plugin/marketplace.json`、各プラグインの `.claude-plugin/plugin.json` と `.codex-plugin/plugin.json`、`CHANGELOG.md`。上げたら `python3 scripts/check.py` がずれを見つけないことを確かめる。

## テスト

```bash
python3 -m unittest discover -s plugins/grip-for-readers/tests
python3 -m unittest discover -s scripts/tests
python3 scripts/check.py
```

標準ライブラリだけで書き、追加のパッケージは入れない。
