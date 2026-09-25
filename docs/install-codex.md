# Codex に入れる

reader-first は、AIが長い報告や第三者に渡す文面を書くとき、読み手と、読み終えた後に取ってほしい行動を先に決めさせるスキルと、下書きを出す前に読み手の立場の別のAIに読ませる「試し読み」のフックからなる。この手順で、Codex に reader-first を入れ、試し読みが動いたことを確かめられる。所要時間は5分ほどである。Codex では、入れたあとにフックを「信頼する」操作が要る。これをしないと、スキルだけが動き、試し読みは動かない。入れる前に、どこに何を送り、何が手元に残るかを [privacy-and-cost.md](privacy-and-cost.md) で確かめてほしい。

## 必要なもの

- Codex CLI（0.144.0 で動作を確かめた。デスクトップ版の Codex では確かめていない）
- `python3`（標準ライブラリだけを使う）
- シェルから `codex` コマンドが呼べること。試し読み役は、フックが `codex exec` で呼び出す
- Codex のフック機能が有効であること（既定で有効。`codex features list` の `hooks` が `true`）

## 入れる

```bash
codex plugin marketplace add buckmoon/agent-plugins
codex plugin add reader-first@buckmoon
```

## フックを信頼する

Codex は、プラグインのフックを、利用者が信頼するまで動かさない。

1. Codex を対話モードで起動する（`codex`）
2. `/hooks` を開く
3. reader-first のフック2件（PreToolUse と Stop）を信頼する

`codex exec` のような非対話の実行では、信頼していないフックは知らせなしに読み飛ばされる。プラグインを更新してフックの命令が変わったときも、もう一度信頼が要る。

## 動いたことを確かめる

Codex に次のように頼む。

```text
reader-first スキルの手順で、このフォルダの中身を依頼者の私に向けて400字以上で報告してください。
```

AIがスキルを読み、一時フォルダの下の `reader-first-drafts/` に下書きを新しいファイルとして書く。一時フォルダは環境変数 `TMPDIR` の場所で、空なら `/tmp` である（`ls "${TMPDIR:-/tmp}/reader-first-drafts/"` で下書きを見られる）。書き込みの直前に試し読みが動き、10秒前後待たされる。読み手が引っかかる文があれば、書き込みが1回止められ、AIが質問に答える形で書き直す。引っかかる文がなければ、止められずにそのまま書き込まれる。どちらも正常な動きである。

動いたかどうかは、記録の中の試し読みの行で分かる。

```bash
grep '"mode": "pre"' ~/.codex/cold-read-gate/log.jsonl | tail -1
```

出た行の `"at"` が頼んだ時刻であれば、試し読みが動いている。何も出ないとき、または `log.jsonl` がないときは、試し読みが動いていない。まず `/hooks` でフックを信頼したかを確かめる。

## Claude Code 版との違い

- **試し読み役のモデル。** 試し読み役は、利用者の `~/.codex/config.toml` を読まずに起動する（試し読み役の中でフックがもう一度動かないようにするため）。そのため、config.toml で選んだモデルではなく、Codex の既定のモデルを使う。変えたいときは環境変数 `COLD_READ_GATE_MODEL` にモデル名を入れる。
- **下書きの書き換えは試し読みしない。** AIが既存の下書きを直したときは、試し読みされずにそのまま通る。Codex はファイルの書き込みを差分としてフックに渡すので、全文が分かるのは新しいファイルを作るときだけだからである。スキルは、下書きを毎回新しいファイル名で書くよう指示している。

## 更新する・外す

```bash
codex plugin marketplace upgrade buckmoon    # 目録を最新にする
codex plugin add reader-first@buckmoon       # 最新の版を入れ直す
codex plugin remove reader-first@buckmoon
```

外しても、`~/.codex/cold-read-gate/` の記録は残る。要らなければ消してよい。一時的に止めたいだけなら、Codex を起動する前に環境変数 `COLD_READ_GATE=0` を設定する。
