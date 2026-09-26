"""送る前の試し読み（フック）の、Claude Code と Codex で共通の部分。

道具ごとの違い（止める対象の見分け方、会話記録の読み方、試し読み役の呼び方、止め方）は
host として渡す。host は claude_code.py と codex.py にある。

  pre   下書きファイルへの書き込みと GitHub への投稿本文を、別のAIに読ませる。
        引っかかれば書き込み・投稿を止め、質問を返す
  stop  依頼者への長い文章が下書きを経ずに出たかを記録するだけ（止めない）

読み手は下書きのファイル名の先頭で決まる（slack-… / email-… / github-… / doc-…、それ以外は依頼者）。
「そのまま出すか、下書きにするか」の判断は grip-for-readers スキルが行う。
同じ依頼（ターン）で止めるのは種類ごとに1回だけ。失敗したら止めない（fail open）。
無効化: 環境変数 GRIP_FOR_READERS=0
"""
import hashlib
import json
import os
import sys
import time

MIN_CHARS = int(os.environ.get('GRIP_FOR_READERS_MIN_CHARS', '400'))
RECORD_LIMIT = 30000
TIMEOUT_SEC = 150
CHILD_ENV = 'GRIP_FOR_READERS_CHILD'
DRAFT_MARK = '/grip-for-readers-drafts/'  # 下書きは一時フォルダの下の grip-for-readers-drafts/ に置く
DRAFT_HEAD = 200  # 下書きを通したかは、下書きの冒頭のこの字数が報告に含まれるかで見る

NOT_IN_CHAT = 'エージェントと依頼者のチャットのやり取りは見ていません。'
AUDIENCE = {
    'requester': ('AIエージェントが依頼者（このチャットの利用者）に向けて書いた文章',
                  '依頼者が見たのは、渡された「これまでのやり取り」だけです。',
                  '読んだ直後に、依頼者は何を返せばよいか（続けてよいと答える／選ぶ／操作する／何も返さない など）が分かるか'),
    'github': ('AIエージェントがGitHubのissueやPRに投稿しようとしている文章',
               '読み手は、このリポジトリの開発者やレビュアーです。' + NOT_IN_CHAT,
               '読んだ直後に、読み手は何をすればよいか（レビューする／判断する／知っておくだけ など）が分かるか'),
    'slack': ('依頼者がSlackに投稿するためにAIエージェントが書いた文面',
              '読み手は、依頼者のチームのメンバーに限らず、ほかの部署の人や社外の顧客を含むプロジェクトの関係者です。チーム内や社内だけで通じる呼び名は知りません。' + NOT_IN_CHAT,
              '読んだ直後に、読み手は何をすればよいか（返信する／判断する／作業する／知っておくだけ など）が分かるか'),
    'email': ('依頼者がメールで送るためにAIエージェントが書いた文面',
              '読み手は、依頼者のメールの受け手で、社外の人のこともあります。' + NOT_IN_CHAT,
              '読んだ直後に、受け手は何をすればよいか（返信する／日程を決める／確認する／知っておくだけ など）が分かるか'),
    'doc': ('AIエージェントが書いた、ファイルとして残す文書（手順書・設計メモ・議事録など）',
            '読み手は、後日この文書を開くチームのメンバーや依頼者自身です。書かれた当時の作業の経緯は覚えていません。' + NOT_IN_CHAT,
            '読んだ直後に、読み手はこの文書で何ができるか（手順を実行する／判断する／経緯を知る など）が分かるか'),
}
# GitHub の MCP の道具で投稿するときの、本文の項目名
GITHUB_BODY_TOOLS = {
    'mcp__github__add_issue_comment': 'body',
    'mcp__github__add_reply_to_pull_request_comment': 'body',
    'mcp__github__create_pull_request': 'body',
    'mcp__github__update_pull_request': 'body',
    'mcp__github__issue_write': 'body',
}
DRAFT_READERS = ('slack', 'email', 'github', 'doc', 'requester')
READER_NAME = {'requester': '依頼者', 'github': 'issueやPRの読み手', 'slack': 'Slackの読み手',
               'email': 'メールの受け手', 'doc': '文書の読み手'}


def reader_prompt(audience):
    what, who, q1 = AUDIENCE[audience]
    return f"""あなたは「試し読み役」です。{what}を、読み手の立場で読みます。
{who}エージェントが作業中に読んだファイル、ツールの出力、途中の判断は見ていません。
あなた自身の一般知識で意味が分かっても、渡された記録に出てこず本文の中で説明もない識別子・ファイル名・内部の呼び名・記録にない出来事は、読み手が知らないものとして扱います。一般的な開発者が確実に知る語（API、JSON、PRなど）は除きます。

次の二つを判定し、JSONだけを出力してください。説明文やコードフェンスは付けないでください。
1. {q1}
2. 読み手が引っかかる・読み直す・このままでは動けない文。多くても5つ。本当に引っかかる文だけを挙げる

出力形式:
{{"reply_clear": true または false, "expected_reply": "読み手が返す・取ると思われる一言、分からなければ空文字", "stuck": [{{"quote": "引っかかる文の抜粋（30字以内）", "question": "読み手が書き手に返したい質問"}}]}}"""


def reader_body(record, text, audience):
    if audience == 'requester':
        return f"# これまでのやり取り\n\n{record or '（なし）'}\n\n# 読む文章\n\n{text}"
    return f"# 読む文章\n\n{text}"


def format_record(ev):
    record = '\n\n'.join(('【依頼者】\n' if r == 'requester' else '【AI】\n') + t for r, t in ev)
    if len(record) > RECORD_LIMIT:
        record = '（前略）\n' + record[-RECORD_LIMIT:]
    return record


def split_record_and_report(ev, last_message=None):
    """最後の依頼者発言より後のAI本文を報告、それより前を記録とする。"""
    last_req = max((i for i, (r, _) in enumerate(ev) if r == 'requester'), default=-1)
    report = '\n\n'.join(t for r, t in ev[last_req + 1:] if r == 'assistant')
    if last_message and len(last_message.strip()) >= len(report):
        report = last_message.strip()
    return format_record(ev[:last_req + 1]), report


def turn_key(ev):
    reqs = [t for r, t in ev if r == 'requester']
    return f"{len(reqs)}:{hashlib.sha1((reqs[-1] if reqs else '').encode()).hexdigest()[:12]}"


def draft_reader(path):
    """下書きのファイル名の先頭（slack- など）から読み手を返す。該当しなければ依頼者。"""
    name = os.path.basename(path)
    return next((r for r in DRAFT_READERS if name.startswith(r + '-')), 'requester')


def is_draft_path(path):
    return DRAFT_MARK in '/' + (path or '').replace('\\', '/').lstrip('/')


def github_post(tool_name, tool_input):
    """GitHub への投稿なら ('post', 'github', 本文) を返す。"""
    field = GITHUB_BODY_TOOLS.get(tool_name)
    if field and isinstance(tool_input, dict) and isinstance(tool_input.get(field), str):
        return 'post', 'github', tool_input[field]
    return None


def parse_reader_output(raw):
    s = raw.strip()
    start, end = s.find('{'), s.rfind('}')
    if start < 0 or end < 0:
        raise ValueError('no JSON in reader output')
    return json.loads(s[start:end + 1])


def should_block(verdict):
    return (not verdict.get('reply_clear', True)) or bool(verdict.get('stuck'))


def block_reason(verdict, via, reader):
    who = READER_NAME[reader]
    lines = [f'送る前の試し読みで、{who}の立場から次の点に引っかかりました。',
             '作業の文脈を持つあなたが質問に答える形で直してください（grip-for-readers スキルに従う）。']
    if via == 'post':
        lines.append('本文を直してから、もう一度投稿してください。')
    elif reader == 'requester':
        lines.append('直した版を下書きフォルダ（grip-for-readers-drafts）に新しいファイル名で書き直してから、その内容をチャットに出してください。')
    else:
        lines.append(f'直した版を下書きフォルダ（grip-for-readers-drafts）に、先頭が「{reader}-」の新しいファイル名で書き直してから、本来の送り先や保存先に使ってください。')
    lines += ['止めるのはこの1回だけです。答えられない質問は「まだ分かっていないこと」として残してください。', '']
    if not verdict.get('reply_clear', True):
        lines.append(f'- 読んだ直後に、{who}が何をすればよいか分かりません。冒頭と最後で、返してほしいことをはっきり書いてください。')
    for s in (verdict.get('stuck') or [])[:5]:
        lines.append(f"- 「{s.get('quote', '')}」→ {s.get('question', '')}")
    return '\n'.join(lines)


def run_reader(record, text, audience, host):
    raw = host.ask(reader_prompt(audience), reader_body(record, text, audience))
    return parse_reader_output(raw)


def child_env():
    return dict(os.environ, **{CHILD_ENV: '1'})


def gate_dir(host):
    return os.environ.get('GRIP_FOR_READERS_HOME') or os.path.expanduser(host.HOME)


def log(host, entry):
    entry = dict(entry, at=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry.get('ts', time.time()))))
    try:
        os.makedirs(gate_dir(host), exist_ok=True)
        with open(os.path.join(gate_dir(host), 'log.jsonl'), 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except OSError:
        pass


def load_state(host, name):
    try:
        with open(os.path.join(gate_dir(host), name)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(host, name, state):
    try:
        os.makedirs(gate_dir(host), exist_ok=True)
        with open(os.path.join(gate_dir(host), name), 'w') as f:
            json.dump(dict(list(state.items())[-200:]), f, ensure_ascii=False)
    except OSError:
        pass


def already_blocked(host, key):
    """同じターン・同じ種類で一度止めていれば True。初回なら記録して False。"""
    state = load_state(host, 'state.json')
    if state.get(key):
        return True
    state[key] = time.time()
    save_state(host, 'state.json', state)
    return False


def remember_draft(host, session, text):
    """会話ごとに、依頼者向けの最後の下書きの冒頭を覚える。応答の終わりに、下書きを通したかを見るのに使う。"""
    state = load_state(host, 'last_drafts.json')
    state.pop(str(session), None)
    state[str(session)] = text.strip()[:DRAFT_HEAD]
    save_state(host, 'last_drafts.json', state)


def report_was_drafted(host, session, report):
    """その会話で最後に書いた依頼者向けの下書きの冒頭が、報告に含まれるか（下書き経由で出したかの目安）。
    報告には、最終回答の前に出した途中経過の文も含まれるので、先頭の一致では見ない。"""
    draft = load_state(host, 'last_drafts.json').get(str(session))
    return bool(draft) and draft in report


def read_events(inp, host):
    try:
        with open(inp.get('transcript_path') or '') as f:
            return host.visible_events(f)
    except OSError:
        return []


def pre(inp, host):
    target = host.target_of(inp.get('tool_name', ''), inp.get('tool_input') or {})
    if not target:
        return None
    via, reader, text = target
    if via == 'draft' and reader == 'requester':
        remember_draft(host, inp.get('session_id'), text)
    if len(text) < MIN_CHARS:
        return None
    ev = read_events(inp, host)
    key = f"{inp.get('session_id')}|{turn_key(ev)}|{via}:{reader}"
    started = time.time()
    try:
        verdict = run_reader(format_record(ev), text, reader, host)
    except Exception as e:  # fail open
        log(host, {'ts': started, 'mode': 'pre', 'via': via, 'reader': reader, 'session': inp.get('session_id'),
                   'error': str(e)[:500]})
        return None
    blocked = should_block(verdict) and not already_blocked(host, key)
    log(host, {'ts': started, 'mode': 'pre', 'via': via, 'reader': reader, 'session': inp.get('session_id'),
               'chars': len(text), 'seconds': round(time.time() - started, 1), 'blocked': blocked,
               'verdict': verdict, 'text': text})
    if not blocked:
        return None
    return host.deny(block_reason(verdict, via, reader))


def stop(inp, host):
    """依頼者への長い文章が下書きを経ずに出たかを記録する。止めない。"""
    ev = read_events(inp, host)
    _, report = split_record_and_report(ev, inp.get('last_assistant_message'))
    if len(report) >= MIN_CHARS:
        log(host, {'ts': time.time(), 'mode': 'stop', 'session': inp.get('session_id'), 'chars': len(report),
                   'drafted': report_was_drafted(host, inp.get('session_id'), report)})
    return None


def main(argv, host):
    if os.environ.get('GRIP_FOR_READERS') == '0' or os.environ.get(CHILD_ENV):
        return 0
    try:
        inp = json.load(sys.stdin)
    except ValueError:
        return 0
    mode = argv[1] if len(argv) > 1 else 'stop'
    out = pre(inp, host) if mode == 'pre' else stop(inp, host)
    if out is None:
        out = getattr(host, 'NOTHING', None)
    if out is not None:
        print(json.dumps(out, ensure_ascii=False))
    return 0
