/*!
 * mock-notes.js — HTML モックの画面に「修正済み・要解決・要確認」の注記を浮かべる部品
 * 依存なし。1ファイルの HTML に <script> ごと貼って使える。使い方は reference.md を参照。
 * MIT License (c) buckmoon
 */
(function (global) {
  'use strict';

  var ICON = {
    fixed: '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z"/></svg>',
    conflict: '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M13 14h-2V9h2m0 9h-2v-2h2M1 21h22L12 2 1 21z"/></svg>',
    assumption: '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M10 19h3v3h-3v-3m2-17c5.35.22 7.68 5.62 4.5 9.67-.83 1-2.17 1.66-2.83 2.5C13 15 13 16 13 17h-3c0-1.67 0-3.08.67-4.08.66-1 2-1.59 2.83-2.25C15.92 8.43 15.32 5.26 12 5a3 3 0 0 0-3 3H6a6 6 0 0 1 6-6z"/></svg>',
    close: '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
    grip: '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M9 3h2v2H9V3m4 0h2v2h-2V3M9 7h2v2H9V7m4 0h2v2h-2V7m-4 4h2v2H9v-2m4 0h2v2h-2v-2m-4 4h2v2H9v-2m4 0h2v2h-2v-2m-4 4h2v2H9v-2m4 0h2v2h-2v-2z"/></svg>',
    down: '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M7 10l5 5 5-5z"/></svg>',
    cursor: '<svg width="26" height="30" viewBox="0 0 26 30" aria-hidden="true"><path d="M3 2 L3 24 L9 18.5 L13 28 L17 26.3 L13 17 L21 17 Z" fill="#111" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>'
  };
  var KINDS = {
    fixed: { label: '修正済み', color: '#23923f' },
    conflict: { label: '要解決', color: '#d93a3a' },
    assumption: { label: '要確認', color: '#b26a00' }
  };
  var MENU_ORDER = ['conflict', 'assumption', 'fixed'];
  var SVGNS = 'http://www.w3.org/2000/svg';

  var CSS = [
    '.mn-root{position:fixed;inset:0;pointer-events:none;z-index:2147483000;font:12.5px/1.6 -apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;color:#1f2328}',
    '.mn-root *{box-sizing:border-box}',
    '.mn-svg{position:absolute;left:0;top:0;width:100%;height:100%;overflow:visible;pointer-events:none}',
    '.mn-arrow{fill:none;stroke-width:2;stroke-linecap:round}',
    '.mn-pin{position:absolute;width:24px;height:24px;padding:0;border-radius:50% 50% 50% 0;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.25);color:#fff;display:flex;align-items:center;justify-content:center;transform:translate(0,-100%);transform-origin:0 100%;cursor:pointer;pointer-events:auto;transition:transform .12s}',
    '.mn-pin:hover{transform:translate(0,-100%) scale(1.15)}',
    '.mn-pin.closed{background:#fff!important}',
    '.mn-card{position:absolute;width:340px;display:flex;gap:10px;padding:10px 14px 12px 10px;background:#fff;border:1px solid;border-radius:10px;box-shadow:0 12px 32px rgba(0,0,0,.18),0 2px 6px rgba(0,0,0,.08);cursor:grab;user-select:none;touch-action:none;pointer-events:auto}',
    '.mn-card.conflict{width:460px;background:#fffbfb}',
    '.mn-card.assumption{background:#fffdf7}',
    '.mn-card.dragging{cursor:grabbing;box-shadow:0 18px 44px rgba(0,0,0,.26)}',
    '.mn-card.mn-flash{animation:mn-flash 1.2s ease-in-out 2}',
    '@keyframes mn-flash{50%{box-shadow:0 0 0 6px rgba(47,111,214,.45),0 12px 32px rgba(0,0,0,.18)}}',
    '.mn-card .mn-leaf{width:24px;height:24px;border-radius:50% 50% 50% 0;flex-shrink:0;color:#fff;display:flex;align-items:center;justify-content:center}',
    '.mn-card .mn-b{flex:1;min-width:0}',
    '.mn-card .mn-h{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center;margin-bottom:2px;padding-right:44px}',
    '.mn-card .mn-no{font-weight:800;color:#111}',
    '.mn-card .mn-tag{font-weight:700;font-size:11px;padding:1px 8px;border-radius:10px;color:#fff}',
    '.mn-card .mn-from{color:#59636e;font-size:11px}',
    '.mn-card .mn-title{font-weight:700;width:100%}',
    '.mn-card .mn-tools{position:absolute;right:6px;top:6px;display:flex;gap:2px;align-items:center;color:#8c959f}',
    '.mn-card .mn-x{border:none;background:transparent;width:24px;height:24px;border-radius:4px;cursor:pointer;color:#59636e;display:flex;align-items:center;justify-content:center;padding:0}',
    '.mn-card .mn-x:hover{background:#eef0f3;color:#111}',
    '.mn-rows{display:grid;grid-template-columns:auto 1fr;gap:3px 8px;margin:4px 0 0}',
    '.mn-rows dt{font-size:11px;font-weight:700;color:#59636e;background:#eef0f3;border-radius:3px;padding:0 6px;height:18px;line-height:18px;margin-top:1px;white-space:nowrap}',
    '.mn-rows dd{margin:0;white-space:pre-wrap}',
    '.mn-cols{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}',
    '.mn-col{background:#f3f4f6;border-radius:6px;padding:6px 10px;white-space:pre-wrap}',
    '.mn-col b{display:block;font-size:11.5px}',
    '.mn-bar{position:fixed;left:12px;bottom:12px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;background:#fff8c5;border:1px solid #e6d27a;border-radius:8px;padding:4px 8px;box-shadow:0 4px 14px rgba(0,0,0,.12);pointer-events:auto;font-size:12px;max-width:calc(100vw - 24px)}',
    '.mn-bar.mounted{position:relative;left:auto;bottom:auto;box-shadow:none}',
    '.mn-bar button{font:inherit;background:#fff;border:1px solid #d9c46a;border-radius:4px;padding:1px 8px;cursor:pointer;color:#5a4a00;display:inline-flex;align-items:center;gap:2px}',
    '.mn-bar .mn-menu-btn{font-weight:700}',
    '.mn-lg{font-size:11px;font-weight:700;color:#fff;padding:0 7px;border-radius:9px;cursor:help}',
    '.mn-menu{position:absolute;left:0;bottom:calc(100% + 6px);width:480px;max-width:calc(100vw - 24px);max-height:70vh;overflow:auto;background:#fff;border:1px solid #d1d9e0;border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.2);color:#111}',
    '.mn-bar.mounted .mn-menu{bottom:auto;top:calc(100% + 6px)}',
    '.mn-gh{position:sticky;top:0;background:#eef0f3;padding:6px 12px;font-size:11px;font-weight:700;color:#59636e;border-bottom:1px solid #d1d9e0}',
    '.mn-mi{display:flex!important;gap:10px;align-items:flex-start!important;width:100%;text-align:left;border:none!important;border-bottom:1px solid #e3e6ea!important;border-radius:0!important;background:#fff!important;padding:8px 12px!important;cursor:pointer;color:#111!important}',
    '.mn-mi:hover{background:#eef4ff!important}',
    '.mn-mi .mn-leaf{width:18px;height:18px;border-radius:50% 50% 50% 0;flex-shrink:0;color:#fff;display:flex;align-items:center;justify-content:center;margin-top:1px}',
    '.mn-mi .mn-t{display:flex;flex-direction:column;min-width:0}',
    '.mn-mi .mn-here{font-size:10.5px;background:#fff3b0;color:#5a4a00;border-radius:8px;padding:0 6px;margin-left:6px;font-weight:700}',
    '.mn-mi .mn-sub{color:#59636e}',
    '.mn-copy{position:fixed;left:12px;bottom:56px;width:min(560px,calc(100vw - 24px));background:#fff;border:1px solid #d1d9e0;border-radius:8px;box-shadow:0 16px 40px rgba(0,0,0,.2);padding:10px;pointer-events:auto}',
    '.mn-copy textarea{width:100%;height:240px;font:12px/1.5 ui-monospace,Menlo,monospace}',
    '.mn-copy .mn-ch{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;font-weight:700}',
    '.mn-block{position:fixed;inset:0;pointer-events:auto;cursor:progress;background:transparent}',
    '.mn-ring{position:fixed;border:2px solid #2f6fd6;border-radius:6px;box-shadow:0 0 0 4px rgba(47,111,214,.18);transition:all .35s ease;display:none}',
    '.mn-cursor{position:fixed;transition:left .8s cubic-bezier(.4,0,.2,1),top .8s cubic-bezier(.4,0,.2,1);filter:drop-shadow(0 2px 3px rgba(0,0,0,.35))}',
    '.mn-ripple{position:fixed;width:0;height:0}',
    '.mn-ripple.go::after{content:"";position:absolute;left:-18px;top:-18px;width:36px;height:36px;border-radius:50%;background:rgba(47,111,214,.35);animation:mn-ripple .5s ease-out forwards}',
    '@keyframes mn-ripple{from{transform:scale(.3);opacity:1}to{transform:scale(1.6);opacity:0}}',
    '.mn-cap{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);width:min(560px,calc(100vw - 32px));background:#1f2430;color:#fff;border-radius:10px;box-shadow:0 12px 32px rgba(0,0,0,.3);padding:12px 16px;font-size:13px;pointer-events:auto}',
    '.mn-cap .mn-ch{font-size:11px;color:#b9c0cf;margin-bottom:4px;padding-right:120px}',
    '.mn-cap .mn-cb{font-size:14px;font-weight:700;display:flex;gap:10px;align-items:center}',
    '.mn-cap .mn-step{background:#2f6fd6;border-radius:10px;padding:1px 9px;font-size:11px;white-space:nowrap}',
    '.mn-cap button{position:absolute;right:12px;top:10px;background:transparent;border:1px solid #5b6274;color:#dfe3ea;border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer}'
  ].join('\n');

  var S = null;
  var listening = false;

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function hash(t) { var h = 5381; for (var i = 0; i < t.length; i++) h = ((h << 5) + h + t.charCodeAt(i)) | 0; return (h >>> 0).toString(36); }
  function load(k, d) { try { var v = JSON.parse(localStorage.getItem(S.opts.key + k)); return v == null ? d : v; } catch (e) { return d; } }
  function store(k, v) { try { localStorage.setItem(S.opts.key + k, JSON.stringify(v)); } catch (e) { /* 保存できなくても動かす */ } }
  function noOf(note) { return S.notes.indexOf(note) + 1; }
  function kindOf(note) { return KINDS[note.kind] ? note.kind : 'fixed'; }
  // 中身が変わった注記は、隠した状態や動かした位置を引き継がない
  function pidOf(note) { var c = {}; for (var k in note) if (k !== 'path') c[k] = note[k]; return note.id + ':' + hash(JSON.stringify(c)); }
  function mine(node) { return !!node && ((S.root && S.root.contains(node)) || (S.bar && S.bar.contains(node))); }

  function visibleEl(sel) {
    var el; try { el = document.querySelector(sel); } catch (e) { return null; }
    if (!el || mine(el)) return null;
    var r = el.getBoundingClientRect();
    return el.getClientRects().length && (r.width > 0 || r.height > 0) ? el : null;
  }
  function shoulderRect(el) {
    if (/^(BUTTON|INPUT|SELECT|TEXTAREA|IMG|SVG|CANVAS|VIDEO)$/i.test(el.tagName)) return el.getBoundingClientRect();
    var rg = document.createRange(); rg.selectNodeContents(el);
    var r = rg.getBoundingClientRect();
    return r.width > 0 ? r : el.getBoundingClientRect();
  }
  function intersects(a, b, m) { m = m || 0; return a.left < b.right + m && a.right + m > b.left && a.top < b.bottom + m && a.bottom + m > b.top; }

  // ---------- カードの中身 ----------
  function rows(pairs) {
    return '<dl class="mn-rows">' + pairs.filter(function (p) { return p[1]; }).map(function (p) { return '<dt>' + esc(p[0]) + '</dt><dd>' + esc(p[1]) + '</dd>'; }).join('') + '</dl>';
  }
  function cardHtml(note) {
    var k = kindOf(note), c = KINDS[k].color;
    var head = '<div class="mn-h"><span class="mn-no">#' + noOf(note) + '</span><span class="mn-tag" style="background:' + c + '">' + KINDS[k].label + '</span>' +
      (note.from ? '<span class="mn-from">' + esc(note.from) + '</span>' : '') +
      (k === 'conflict' && note.title ? '<span class="mn-title">' + esc(note.title) + '</span>' : '') + '</div>';
    var body;
    if (k === 'conflict') {
      body = rows([['場所', note.where]]) +
        '<div class="mn-cols">' + (note.opinions || []).map(function (o) { return '<div class="mn-col"><b>' + esc(o.who) + '</b>' + esc(o.says) + '</div>'; }).join('') + '</div>' +
        rows([['決めてほしいこと', note.ask]]);
    } else if (k === 'assumption') {
      body = rows([['場所', note.where], ['仮に置いた内容', note.what], ['確かめたいこと', note.ask]]);
    } else {
      body = rows([['場所', note.where], ['変更', note.what]]);
    }
    return '<span class="mn-tools"><span title="ドラッグで移動">' + ICON.grip + '</span><button type="button" class="mn-x" data-mn="close" title="この注記を隠す（リーフを押すと再表示）">' + ICON.close + '</button></span>' +
      '<span class="mn-leaf" style="background:' + c + '">' + ICON[k] + '</span><div class="mn-b">' + head + body + '</div>';
  }

  // ---------- 道具の帯と一覧 ----------
  function hiddenCount() { var n = 0; S.notes.forEach(function (x) { if (S.hidden[pidOf(x)]) n++; }); return n; }
  function renderBar() {
    if (!S.bar) return;
    var hc = hiddenCount();
    var legend = ['fixed', 'conflict', 'assumption'].filter(function (k) { return S.notes.some(function (n) { return kindOf(n) === k; }); }).map(function (k) {
      var tip = k === 'fixed' ? (S.opts.baseline ? S.opts.baseline + ' からの変更' : '前の版からの変更') : k === 'conflict' ? '意見が分かれていて、決めてほしい点' : '作り手が仮に置いた内容で、確かめてほしい点';
      return '<span class="mn-lg" style="background:' + KINDS[k].color + '" title="' + esc(tip) + '">' + KINDS[k].label + '</span>';
    }).join('');
    S.bar.innerHTML = '<span style="position:relative"><button type="button" class="mn-menu-btn" data-mn="menu" aria-expanded="' + S.menu + '">注記（' + S.notes.length + '）' + ICON.down + '</button>' + (S.menu ? menuHtml() : '') + '</span>' +
      legend +
      '<button type="button" data-mn="toggle">' + (S.show ? '注記を隠す' : '注記を表示') + '</button>' +
      (S.show ? '<button type="button" data-mn="reset" title="ドラッグで動かした注記を元の位置に戻す">配置を戻す</button>' : '') +
      (S.show && hc ? '<button type="button" data-mn="unhide">隠した注記を表示（' + hc + '）</button>' : '') +
      '<button type="button" data-mn="copy" title="注記の一覧を文字で書き出す（Slack や AI に渡す用）">文字で書き出す</button>';
  }
  function menuHtml() {
    return '<div class="mn-menu" role="menu">' + MENU_ORDER.map(function (k) {
      var list = S.notes.filter(function (n) { return kindOf(n) === k; });
      if (!list.length) return '';
      return '<div class="mn-gh">' + KINDS[k].label + '（' + list.length + '）</div>' + list.map(function (n) {
        var here = !!visibleEl(n.target);
        return '<button type="button" class="mn-mi" role="menuitem" data-mn="goto" data-id="' + esc(n.id) + '"><span class="mn-leaf" style="background:' + KINDS[k].color + '">' + ICON[k] + '</span>' +
          '<span class="mn-t"><b>#' + noOf(n) + ' ' + esc(n.screen || '') + (here ? '<span class="mn-here">このページ</span>' : '') + '</b><span class="mn-sub">' + (k === 'conflict' && n.title ? esc(n.title) + '：' : '') + esc(n.where || '') + '</span></span></button>';
      }).join('');
    }).join('') + '</div>';
  }

  // ---------- 配置 ----------
  function schedule() {
    if (!S || S.raf) return;
    S.raf = requestAnimationFrame(function () { S.raf = 0; if (!S.dragging) layout(); });
  }
  function ensureBar() {
    if (S.bar && S.bar.isConnected) return;
    var host = S.opts.mount ? (typeof S.opts.mount === 'string' ? document.querySelector(S.opts.mount) : S.opts.mount) : null;
    if (!S.bar) { S.bar = document.createElement('div'); S.bar.className = 'mn-bar' + (host ? ' mounted' : ''); bindUi(S.bar); renderBar(); }
    (host || S.root).appendChild(S.bar);
  }
  function removeEls(id) {
    var e = S.els[id]; if (!e) return;
    [e.pin, e.card, e.path].forEach(function (x) { if (x && x.parentNode) x.parentNode.removeChild(x); });
    delete S.els[id];
  }
  function layout() {
    if (!S) return;
    ensureBar();
    var vw = document.documentElement.clientWidth || innerWidth, narrow = vw < 720;
    var alive = {};
    var items = [];
    // ダイアログが開いている間は、その中の注記だけを出す（裏の画面の注記は暗い背景の上でうるさい）
    var dialogs = Array.prototype.filter.call(document.querySelectorAll('[role="dialog"], dialog[open], .modal'), function (d) {
      return !mine(d) && d.getClientRects().length > 0;
    });
    S.notes.forEach(function (note) {
      if (!S.show) return;
      var el = visibleEl(note.target);
      if (!el) return;
      if (dialogs.length && !dialogs.some(function (d) { return d.contains(el); })) return;
      var id = note.id, pid = pidOf(note), k = kindOf(note);
      alive[id] = true;
      var e = S.els[id] || (S.els[id] = {});
      var sr = shoulderRect(el);
      var px = Math.min(Math.max(sr.right - 4, 4), vw - 30), py = sr.top + 4;
      if (!e.pin) {
        e.pin = document.createElement('button'); e.pin.type = 'button'; e.pin.className = 'mn-pin'; e.pin.dataset.mn = 'pin'; e.pin.dataset.id = id;
        e.pin.innerHTML = ICON[k];
        S.layer.appendChild(e.pin);
      }
      var hidden = !!S.hidden[pid];
      e.pin.classList.toggle('closed', hidden);
      e.pin.style.background = KINDS[k].color; e.pin.style.color = hidden ? KINDS[k].color : '#fff'; e.pin.style.borderColor = hidden ? KINDS[k].color : '#fff';
      e.pin.setAttribute('aria-pressed', String(!hidden));
      e.pin.title = '注記 #' + noOf(note) + '（' + KINDS[k].label + '）を' + (hidden ? '表示' : '隠す');
      e.pin.style.left = px + 'px'; e.pin.style.top = py + 'px';
      if (hidden) {
        if (e.card) { e.card.remove(); e.card = null; }
        if (e.path) { e.path.remove(); e.path = null; }
        return;
      }
      if (!e.card) {
        e.card = document.createElement('div'); e.card.className = 'mn-card ' + k; e.card.dataset.id = id;
        e.card.style.borderColor = k === 'fixed' ? '#a9d8b5' : k === 'conflict' ? '#f0a3a3' : '#f3c98b';
        e.card.innerHTML = cardHtml(note);
        S.layer.appendChild(e.card);
        enableDrag(e, note);
        e.path = document.createElementNS(SVGNS, 'path'); e.path.setAttribute('class', 'mn-arrow'); e.path.dataset.id = id;
        e.path.setAttribute('stroke', KINDS[k].color); e.path.setAttribute('marker-end', 'url(#mn-head-' + k + ')');
        S.svg.appendChild(e.path);
      }
      e.card.classList.toggle('mn-flash', S.focus === id);
      items.push({ note: note, el: el, e: e, pid: pid, px: px, py: py, tr: el.getBoundingClientRect() });
    });
    Object.keys(S.els).forEach(function (id) { if (!alive[id]) removeEls(id); });

    // 既定の位置：右の余白に縦に並べる。対象やダイアログに重なるときは、その横か下に置く
    items.sort(function (a, b) { return a.tr.top - b.tr.top; });
    // どのカードも、ほかの注記のリーフと対象を覆わないようにする
    var placed = [];
    S.notes.forEach(function (n) {
      var e = S.els[n.id]; if (!e || !e.pin) return;
      var px = parseFloat(e.pin.style.left), py = parseFloat(e.pin.style.top);
      placed.push({ left: px, right: px + 24, top: py - 24, bottom: py });
    });
    items.forEach(function (it) { placed.push({ left: it.tr.left, right: it.tr.right, top: it.tr.top, bottom: it.tr.bottom }); });
    items.forEach(function (it) {
      var card = it.e.card, k = kindOf(it.note);
      var w = k === 'conflict' ? 460 : 340;
      if (narrow) w = Math.min(w, vw - 32);
      card.style.width = w + 'px';
      var saved = S.pos[it.pid], left, top;
      if (saved) { left = it.px + saved.dx; top = it.py + saved.dy; }
      else {
        var dlg = it.el.closest('[role="dialog"], dialog, .modal');
        var avoid = dlg ? dlg.getBoundingClientRect() : it.tr;
        var col = vw - w - 16;
        if (narrow) { left = 16; top = it.tr.bottom + 12; }
        else if (col >= avoid.right + 24) { left = col; top = it.tr.top; }
        else if (dlg) {
          var roomR = vw - avoid.right - 40, roomL = avoid.left - 40;
          if (roomR >= 240) { w = Math.min(w, roomR); left = avoid.right + 24; }
          else if (roomL >= 240) { w = Math.min(w, roomL); left = avoid.left - 24 - w; }
          else left = col;
          card.style.width = w + 'px'; top = it.tr.top;
        } else { left = Math.max(16, Math.min(it.tr.left, col)); top = it.tr.bottom + 12; }
        var h = card.offsetHeight, moved = true;
        while (moved) {
          moved = false;
          for (var i = 0; i < placed.length; i++) {
            if (intersects({ left: left, right: left + w, top: top, bottom: top + h }, placed[i], 12)) { top = placed[i].bottom + 12; moved = true; }
          }
        }
        placed.push({ left: left, right: left + w, top: top, bottom: top + h });
      }
      card.style.left = left + 'px'; card.style.top = top + 'px';
      drawArrow(it.e);
    });
  }
  // カードの縁からリーフまで、ゆるい曲線の矢印を描く
  function drawArrow(e) {
    if (!e.path || !e.card) return;
    var l = parseFloat(e.card.style.left), t = parseFloat(e.card.style.top), w = e.card.offsetWidth, h = e.card.offsetHeight;
    var px = parseFloat(e.pin.style.left) + 12, py = parseFloat(e.pin.style.top) - 12;
    if (px >= l && px <= l + w && py >= t && py <= t + h) { e.path.setAttribute('d', ''); return; }
    var sx = Math.min(Math.max(px, l), l + w), sy = Math.min(Math.max(py, t), t + h);
    var dx = px - sx, dy = py - sy, len = Math.hypot(dx, dy) || 1;
    var ex = px - (dx / len) * 14, ey = py - (dy / len) * 14;
    var cx = (sx + ex) / 2 + (dy / len) * 30, cy = (sy + ey) / 2 - (dx / len) * 30;
    e.path.setAttribute('d', 'M' + sx.toFixed(1) + ',' + sy.toFixed(1) + ' Q' + cx.toFixed(1) + ',' + cy.toFixed(1) + ' ' + ex.toFixed(1) + ',' + ey.toFixed(1));
  }
  function enableDrag(e, note) {
    e.card.addEventListener('pointerdown', function (ev) {
      if (ev.button !== 0 || ev.target.closest('button,a,input,select,textarea')) return;
      ev.preventDefault();
      var sx = ev.clientX, sy = ev.clientY, l0 = parseFloat(e.card.style.left), t0 = parseFloat(e.card.style.top);
      S.dragging = true; e.card.classList.add('dragging');
      if (e.card.setPointerCapture) e.card.setPointerCapture(ev.pointerId);
      function move(m) { e.card.style.left = (l0 + m.clientX - sx) + 'px'; e.card.style.top = (t0 + m.clientY - sy) + 'px'; drawArrow(e); }
      function up() {
        e.card.classList.remove('dragging');
        e.card.removeEventListener('pointermove', move); e.card.removeEventListener('pointerup', up); e.card.removeEventListener('pointercancel', up);
        S.pos[pidOf(note)] = { dx: parseFloat(e.card.style.left) - parseFloat(e.pin.style.left), dy: parseFloat(e.card.style.top) - parseFloat(e.pin.style.top) };
        store('-mn-pos', S.pos); S.dragging = false;
      }
      e.card.addEventListener('pointermove', move); e.card.addEventListener('pointerup', up); e.card.addEventListener('pointercancel', up);
    });
  }

  // ---------- たどり方の再生 ----------
  function labelOf(el) { return (el.textContent || el.value || '').replace(/\s+/g, ' ').trim().slice(0, 30); }
  function sayOf(step, el) {
    if (step.say) return step.say;
    if (step.go) return '画面を開く（' + step.go + '）';
    if (step.select) return '「' + labelOf(el) + '」で「' + step.value + '」を選ぶ';
    return '「' + labelOf(el) + '」を押す';
  }
  async function waitFor(sel, ms) {
    var t0 = Date.now();
    for (;;) { var el = visibleEl(sel); if (el) return el; if (Date.now() - t0 > ms) return null; await sleep(50); }
  }
  function tourUi() {
    if (S.tui) return S.tui;
    function mk(cls, html) { var d = document.createElement('div'); d.className = cls; if (html) d.innerHTML = html; S.root.appendChild(d); return d; }
    S.tui = { block: mk('mn-block'), ring: mk('mn-ring'), ripple: mk('mn-ripple'), cursor: mk('mn-cursor', ICON.cursor), cap: mk('mn-cap') };
    S.tui.cap.addEventListener('click', function (ev) { if (ev.target.closest('[data-mn="skip"]') && S.tour) S.tour.fast = true; ev.stopPropagation(); });
    return S.tui;
  }
  function endTourUi() { if (S.tui) { Object.keys(S.tui).forEach(function (k) { S.tui[k].remove(); }); S.tui = null; } }
  function caption(note, n, text, done) {
    var u = tourUi();
    u.cap.innerHTML = '<div class="mn-ch">注記 #' + noOf(note) + '　' + esc(note.screen || '') + ' を開く手順</div>' +
      '<div class="mn-cb">' + (done ? '<span style="color:#8ce0a3">' + ICON.fixed + '</span>' : '<span class="mn-step">手順 ' + n + '</span>') + esc(text) + '</div>' +
      (done ? '' : '<button type="button" data-mn="skip">スキップしてすぐ開く</button>');
  }
  function perform(step, el) {
    if (step.go) { location.hash = step.go.replace(/^#?/, '#'); return; }
    if (step.select) { el.value = step.value; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); return; }
    el.click();
  }
  // 注記の場所まで、path の手順を順に実行する。animate が真なら、カーソルの動きを見せる
  async function goTo(note, animate) {
    if (S.tour) S.tour.cancelled = true;
    var t = { cancelled: false, fast: !animate };
    S.tour = t; S.lastTour = [];
    document.body.dataset.mnTour = 'running';
    S.menu = false;
    if (animate) { S.show = true; store('-mn-show', true); delete S.hidden[pidOf(note)]; store('-mn-hidden', S.hidden); }
    renderBar(); layout();
    var result = { ok: true, reason: '' };
    try {
      if (animate) {
        var u = tourUi(), from = S.bar.getBoundingClientRect();
        u.cursor.style.transition = 'none'; u.cursor.style.left = (from.left + 40) + 'px'; u.cursor.style.top = (from.top + 10) + 'px';
        caption(note, 0, '開き方を順に見せます', false);
        await sleep(400);
      }
      // 再生では、もう見えていれば手順を飛ばす。検証（animate が偽）では、手順そのものを確かめるため必ずたどる
      if (!animate || !visibleEl(note.target)) {
        var path = note.path || [], n = 0;
        for (var i = 0; i < path.length; i++) {
          if (t.cancelled) return result;
          var step = path[i], sel = step.go ? null : (step.click || step.select);
          var el = sel ? await waitFor(sel, 1500) : null;
          if (sel && !el) {
            if (step.optional) continue;
            result = { ok: false, reason: '手順' + (i + 1) + 'の要素が見つからない: ' + sel };
            break;
          }
          n++;
          var say = sayOf(step, el);
          S.lastTour.push(say);
          if (!t.fast && el) {
            el.scrollIntoView({ block: 'nearest' });
            var r = el.getBoundingClientRect(), tu = tourUi();
            caption(note, n, say, false);
            tu.ring.style.display = 'block';
            tu.ring.style.left = (r.left - 4) + 'px'; tu.ring.style.top = (r.top - 4) + 'px'; tu.ring.style.width = (r.width + 8) + 'px'; tu.ring.style.height = (r.height + 8) + 'px';
            tu.cursor.style.transition = '';
            tu.cursor.style.left = (r.left + Math.min(r.width / 2, 60)) + 'px'; tu.cursor.style.top = (r.top + r.height / 2) + 'px';
            await sleep(900);
            if (!t.fast) {
              tu.ripple.style.left = tu.cursor.style.left; tu.ripple.style.top = tu.cursor.style.top;
              tu.ripple.classList.remove('go'); void tu.ripple.offsetWidth; tu.ripple.classList.add('go');
              await sleep(220);
            }
            tu.ring.style.display = 'none';
          } else if (!t.fast) { caption(note, n, say, false); await sleep(600); }
          if (t.cancelled) return result;
          perform(step, el);
          await sleep(t.fast ? 80 : 650);
        }
      }
      if (result.ok) {
        var target = await waitFor(note.target, 1500);
        if (!target) result = { ok: false, reason: '対象が見つからない: ' + note.target };
        else {
          var count = document.querySelectorAll(note.target).length;
          if (count > 1) result = { ok: false, reason: '対象のセレクタが複数の要素に一致する（' + count + '件）: ' + note.target };
          var tr = target.getBoundingClientRect();
          if (tr.top < 0 || tr.bottom > innerHeight) target.scrollIntoView({ block: 'center' });
        }
      }
      if (animate && !t.cancelled) {
        S.focus = note.id; clearTimeout(S.focusTimer);
        S.focusTimer = setTimeout(function () { if (S) { S.focus = null; layout(); } }, 2600);
        layout();
        var msg = result.ok ? 'ここが注記 #' + noOf(note) + ' の場所です' : '開けませんでした（' + result.reason + '）';
        S.lastTour.push(msg);
        caption(note, 0, msg, true);
        var card = S.els[note.id] && S.els[note.id].card;
        if (card && S.tui) { var cr = card.getBoundingClientRect(); S.tui.cursor.style.left = (cr.left + 30) + 'px'; S.tui.cursor.style.top = (cr.top + 16) + 'px'; }
        await sleep(t.fast ? 300 : 1200);
      }
      return result;
    } finally {
      if (S && S.tour === t) { S.tour = null; endTourUi(); delete document.body.dataset.mnTour; layout(); }
    }
  }

  // ---------- 書き出し ----------
  function exportText() {
    var out = [(document.title || 'モック') + ' の注記（修正済み＝' + (S.opts.baseline || '前の版') + ' からの変更）', ''];
    S.notes.forEach(function (n) {
      var k = kindOf(n);
      out.push('#' + noOf(n) + ' [' + KINDS[k].label + '] ' + (n.screen || '') + (k === 'conflict' && n.title ? ' — ' + n.title : '') + '（id: ' + n.id + '）');
      if (n.where) out.push('  場所: ' + n.where);
      if (k === 'fixed' && n.what) out.push('  変更: ' + n.what);
      if (k === 'assumption' && n.what) out.push('  仮に置いた内容: ' + n.what);
      if (k === 'conflict') (n.opinions || []).forEach(function (o) { out.push('  ' + o.who + ': ' + o.says); });
      if (n.ask) out.push('  ' + (k === 'conflict' ? '決めてほしいこと' : '確かめたいこと') + ': ' + n.ask);
      if (n.from) out.push('  出典: ' + n.from);
    });
    return out.join('\n');
  }
  function showCopy() {
    var text = exportText();
    var done = function () { flashBar('書き出した文字をクリップボードに入れました'); };
    var panel = function () {
      var p = document.createElement('div'); p.className = 'mn-copy';
      p.innerHTML = '<div class="mn-ch"><span>注記の書き出し（選んでコピーしてください）</span><button type="button" class="mn-x" data-mn="copy-close">' + ICON.close + '</button></div><textarea readonly></textarea>';
      p.querySelector('textarea').value = text;
      p.addEventListener('click', function (ev) { if (ev.target.closest('[data-mn="copy-close"]')) p.remove(); ev.stopPropagation(); });
      S.root.appendChild(p); p.querySelector('textarea').select();
    };
    try { navigator.clipboard.writeText(text).then(done, panel); } catch (e) { panel(); }
  }
  function flashBar(msg) {
    var s = document.createElement('span'); s.textContent = msg; s.style.color = '#1a7f37'; s.style.fontWeight = '700';
    S.bar.appendChild(s); setTimeout(function () { s.remove(); }, 2500);
  }

  // ---------- 操作 ----------
  function bindUi(node) {
    node.addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-mn]');
      ev.stopPropagation();
      if (!b) return;
      var act = b.dataset.mn, card = b.closest('.mn-card');
      if (act === 'menu') { S.menu = !S.menu; renderBar(); }
      else if (act === 'goto') { var n = find(b.dataset.id); if (n) goTo(n, true); }
      else if (act === 'toggle') { S.show = !S.show; store('-mn-show', S.show); S.menu = false; renderBar(); layout(); }
      else if (act === 'reset') { S.pos = {}; store('-mn-pos', S.pos); layout(); }
      else if (act === 'unhide') { S.hidden = {}; store('-mn-hidden', S.hidden); renderBar(); layout(); }
      else if (act === 'copy') showCopy();
      else if (act === 'pin' || act === 'close') {
        var note = find(act === 'pin' ? b.dataset.id : card.dataset.id), pid = pidOf(note);
        if (S.hidden[pid]) delete S.hidden[pid]; else S.hidden[pid] = 1;
        store('-mn-hidden', S.hidden); renderBar(); layout();
      }
    });
    node.addEventListener('pointerdown', function (ev) { ev.stopPropagation(); });
  }
  function find(id) { for (var i = 0; i < S.notes.length; i++) if (S.notes[i].id === id) return S.notes[i]; return null; }

  function listen() {
    if (listening) return; listening = true;
    addEventListener('resize', schedule);
    document.addEventListener('scroll', schedule, true);
    addEventListener('hashchange', schedule);
    document.addEventListener('load', function (e) { if (e.target && e.target.tagName === 'LINK') schedule(); }, true);
    document.addEventListener('click', function (ev) {
      if (S && S.menu && !mine(ev.target)) { S.menu = false; renderBar(); }
    }, true);
  }

  function destroy() {
    if (!S) return;
    if (S.mo) S.mo.disconnect();
    if (S.raf) cancelAnimationFrame(S.raf);
    if (S.tour) S.tour.cancelled = true;
    if (S.root) S.root.remove();
    if (S.bar) S.bar.remove();
    delete document.body.dataset.mnTour;
    S = null;
  }

  function init(opts) {
    if (!opts || !opts.key) throw new Error('MockNotes.init: key（localStorage の名前）が要る');
    if (!document.body) { document.addEventListener('DOMContentLoaded', function () { init(opts); }); return; }
    destroy();
    if (!document.getElementById('mn-style')) { var st = document.createElement('style'); st.id = 'mn-style'; st.textContent = CSS; document.head.appendChild(st); }
    S = { opts: opts, notes: (opts.notes || []).slice(), els: {}, raf: 0, menu: false, dragging: false, tour: null, tui: null, focus: null, lastTour: [] };
    var seen = {};
    S.notes.forEach(function (n) {
      if (!n.id || seen[n.id]) throw new Error('MockNotes: 注記の id が無いか重複している: ' + n.id);
      seen[n.id] = true;
    });
    S.pos = load('-mn-pos', {}); S.hidden = load('-mn-hidden', {}); S.show = load('-mn-show', true) !== false;
    S.root = document.createElement('div'); S.root.className = 'mn-root';
    S.svg = document.createElementNS(SVGNS, 'svg'); S.svg.setAttribute('class', 'mn-svg');
    S.svg.innerHTML = '<defs>' + Object.keys(KINDS).map(function (k) {
      return '<marker id="mn-head-' + k + '" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="' + KINDS[k].color + '"/></marker>';
    }).join('') + '</defs>';
    S.layer = document.createElement('div');
    S.root.appendChild(S.svg); S.root.appendChild(S.layer);
    document.body.appendChild(S.root);
    bindUi(S.root);
    ensureBar();
    S.mo = new MutationObserver(function (list) {
      for (var i = 0; i < list.length; i++) if (!mine(list[i].target)) { schedule(); return; }
    });
    S.mo.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['class', 'style', 'hidden', 'open'] });
    listen();
    layout();
  }

  global.MockNotes = {
    init: init,
    refresh: function () { if (S) { renderBar(); layout(); } },
    open: function (id) { var n = S && find(id); return n ? goTo(n, true) : Promise.resolve({ ok: false, reason: 'id が無い: ' + id }); },
    // すべての注記について、path をたどって対象に着けるかを確かめる。結果は [{id, no, ok, reason}]
    verify: async function () {
      var out = [];
      for (var i = 0; i < S.notes.length; i++) {
        var n = S.notes[i], r = await goTo(n, false);
        out.push({ id: n.id, no: i + 1, ok: r.ok, reason: r.reason });
      }
      return out;
    },
    exportText: function () { return S ? exportText() : ''; },
    options: function () { return S && S.opts; },
    destroy: destroy,
    get lastTour() { return S ? S.lastTour.slice() : []; }
  };
})(window);
