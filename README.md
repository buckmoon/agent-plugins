# agent-plugins

Plugins for [Claude Code](https://code.claude.com/) and [Codex](https://developers.openai.com/codex) by buckmoon. The skills and hook prompts are written in Japanese and are meant for Japanese-speaking users.

buckmoon が公開している、Claude Code と Codex の両方で使えるプラグインです。今は reader-first の1つだけを置いています。この README を読めば、自分に合うかを判断し、入れる手順に進めます。

## reader-first

AIが書く長い報告や、Slack・メール・PR に渡す文面を、読み手が読み終えた直後に次の行動を取れるようにするプラグインです。二つの部品からなります。

- **スキル**：書き始める前に、読み手がこれまでに何を見てきたかと、読み終えた直後に何をしてほしいかを決めさせます。そのうえで、冒頭に次の行動を書き、読み手が知らない語を言い換え、短く返せる問いで終えるよう指示します。
- **試し読みフック**：AIが下書きファイルを書く直前と、GitHub の MCP の道具で issue や PR に投稿する直前に、読み手の立場の別のAIに文章を読ませます。読み手が引っかかる文があれば、書き込みや投稿を止め、質問をAIに返して書き直させます。書き直した版も試し読みしますが、止めるのは同じ依頼の中で読み手ごとに1回だけで、2回目は結果を記録してそのまま通します。

下書きは、AIがスキルの指示に従って一時フォルダの下の `reader-first-drafts/` に作ります。利用者が名前を付ける必要はありません。AIは、読み手に合わせてファイル名の先頭を選びます（例：Slack 向けなら `slack-20260925-1430.md`）。先頭なしは依頼者（AIに作業を頼んでいる人）向けで、ほかに `email-`・`github-`・`doc-`（後日文書を開く人）があります。

### 入れる前に知っておくこと

- 試し読みのたびに、利用者のAI（Claude Code なら `claude -p`、Codex なら `codex exec`）を1回呼びます。1回に4〜15秒ほど待たされ、その分の利用量を使います。
- 試し読みした文章の全文を、手元の記録（`~/.claude/cold-read-gate/` または `~/.codex/cold-read-gate/`）に残します。
- `gh` コマンドなどシェルから GitHub に投稿したときは、フックは読みません。

詳しくは [docs/privacy-and-cost.md](docs/privacy-and-cost.md) にあります。

### 入れる

Claude Code（手順の詳細は [docs/install-claude.md](docs/install-claude.md)）：

```text
/plugin marketplace add buckmoon/agent-plugins
/plugin install reader-first@buckmoon
```

Codex（手順の詳細は [docs/install-codex.md](docs/install-codex.md)）：

```bash
codex plugin marketplace add buckmoon/agent-plugins
codex plugin add reader-first@buckmoon
```

Codex では、このあと対話モード（`codex`）で `/hooks` を開き、reader-first のフック2件を信頼するまで、試し読みは動きません。

### 使う

長い報告や、第三者に渡す文面、ファイルとして残す文書を頼むと、AIがスキルを使います。確実に使わせたいときは、「reader-first スキルの手順で書いて」と頼みます。一時的に止めるときは、起動前に環境変数 `COLD_READ_GATE=0` を設定します。

なぜこの形なのか、どんな実験で確かめたか、まだ分かっていないことは [docs/design.md](docs/design.md) にあります。

## 開発

このリポジトリで作業するAI向けの決まりは [AGENTS.md](AGENTS.md) にあります。テストは次のとおりです。

```bash
python3 -m unittest discover -s plugins/reader-first/tests
python3 -m unittest discover -s scripts/tests
python3 scripts/check.py
```

## ライセンス

[MIT](LICENSE)
