# Claude Code に入れる

この手順で、Claude Code に grip-for-readers を入れ、試し読みが動いたことを確かめられる。所要時間は5分ほどである。入れる前に、どこに何を送り、何が手元に残るかを [privacy-and-cost.md](privacy-and-cost.md) で確かめてほしい。

## 必要なもの

- Claude Code（2.1.282 で動作を確かめた）
- `python3`（標準ライブラリだけを使う）
- シェルから `claude` コマンドが呼べること。試し読み役は、フックが `claude -p` で呼び出す

## 入れる

Claude Code の中で、次の2つを順に実行する。

```text
/plugin marketplace add buckmoon/agent-plugins
/plugin install grip-for-readers@buckmoon
```

シェルから入れる場合は次のとおり。

```bash
claude plugin marketplace add buckmoon/agent-plugins
claude plugin install grip-for-readers@buckmoon
```

入れた直後の表示に「Run /reload-plugins to activate.」とあれば `/reload-plugins` を実行する。シェルから入れた場合は、次に起動した Claude Code から有効になる。

## 動いたことを確かめる

途中で、スキルの付属ファイル（readers.md・drafts.md）を読む許可や、一時フォルダの `grip-for-readers-drafts/` に書く許可を求められることがある。どちらも grip-for-readers の手順どおりの操作なので、許可してよい。

Claude Code に次のように頼む。

```text
grip-for-readers スキルの手順で、このフォルダの中身を依頼者の私に向けて400字以上で報告してください。
```

AIがスキルを読み、一時フォルダの下の `grip-for-readers-drafts/` に下書きを書く。一時フォルダは環境変数 `TMPDIR` の場所で、空なら `/tmp` である（`ls "${TMPDIR:-/tmp}/grip-for-readers-drafts/"` で下書きを見られる）。書き込みの直前に試し読みが動き、10秒前後待たされる。読み手が引っかかる文があれば、書き込みが1回止められ、AIが質問に答える形で書き直す。引っかかる文がなければ、止められずにそのまま書き込まれる。どちらも正常な動きである。

動いたかどうかは、記録の中の試し読みの行で分かる。

```bash
grep '"mode": "pre"' ~/.claude/grip-for-readers/log.jsonl | tail -1
```

出た行の `"at"` が頼んだ時刻であれば、試し読みが動いている。何も出ないとき、または `log.jsonl` がないときは、試し読みが動いていない。まず、AIが `grip-for-readers-drafts/` に下書きを書いたかを確かめる。書いていなければ、スキルの手順に従っていない。書いていれば、`/plugin` でプラグインが有効になっているかを確かめる。

## 更新する・外す

```bash
claude plugin marketplace update buckmoon   # 目録を最新にする
claude plugin update grip-for-readers@buckmoon  # プラグインを最新にする
claude plugin uninstall grip-for-readers@buckmoon
```

外しても、`~/.claude/grip-for-readers/` の記録は残る。要らなければ消してよい。一時的に止めたいだけなら、Claude Code を起動する前に環境変数 `GRIP_FOR_READERS=0` を設定する。
