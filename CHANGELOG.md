# 変更履歴

## grip-for-readers 0.3.0（2026-09-26）

- 名前を reader-first から grip-for-readers（Grip for Readers）に変えた。GripSpec と同じ Grip シリーズのスキルセットとして出すため
- 名前に合わせて、次も変えた。入れ直しが要り、前の名前の記録は古いフォルダに残る
  - プラグイン名とスキル名：`reader-first` → `grip-for-readers`（入れるときは `grip-for-readers@buckmoon`）
  - 下書きフォルダ：`reader-first-drafts/` → `grip-for-readers-drafts/`
  - 記録フォルダ：`~/.claude/cold-read-gate/`・`~/.codex/cold-read-gate/` → `~/.claude/grip-for-readers/`・`~/.codex/grip-for-readers/`
  - 環境変数：`COLD_READ_GATE`・`COLD_READ_GATE_MODEL` など → `GRIP_FOR_READERS`・`GRIP_FOR_READERS_MODEL` など
- Codex では、フックの命令が変わったので、`/hooks` でもう一度信頼する必要がある

## reader-first 0.2.0（2026-09-25）

- スキル：同じ文章を何度も直すとき、前の版との違いや直した理由を最新の版の本文に書かない決まりを足した。読み手が前の版を読んでいるときだけ、変わった点を冒頭に短く書く
- プラグインのフォルダに README を足した。目指す状態、依拠している仮説、注意事項をまとめた
- 「読み終えた直後に次の行動を取れる」という言い回しを「読み終えたときに、次に何をすればよいかが分かる」にそろえた

## reader-first 0.1.0（2026-09-25）

最初の公開版。

- スキル reader-first：読み手の手持ちと次の行動を先に決めて書く。読み手は依頼者・GitHub・Slack・メール・文書の5種類
- 試し読みフック：下書きの書き込みと GitHub の MCP の道具での投稿の直前に、読み手の立場の別のAIに読ませ、引っかかる点があれば1回だけ止める
- Claude Code と Codex の両方に対応。下書きは両方とも一時フォルダの下の `reader-first-drafts/` に置く
