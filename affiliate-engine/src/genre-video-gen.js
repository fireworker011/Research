#!/usr/bin/env node
'use strict';

/**
 * ジャンル動画パケットの検品・出力・Grok Bot用「これだけ読んで」ファイル生成。
 * 投稿しない。URLを書かない。
 *
 *   node src/genre-video-gen.js --list
 *   node src/genre-video-gen.js --genre ペット
 *   node src/genre-video-gen.js --genre 婚活 --id konkatsu_app_fatigue_01
 *   node src/genre-video-gen.js --write-agents
 *   node src/genre-video-gen.js --self-test
 */

const fs = require('fs');
const path = require('path');
const { ROOT, OUTPUT_DIR, loadConfig, writeJSON } = require('./util');
const { checkContent } = require('./compliance');
const { PROFILE_CTA, applyProfileCta, youtubeDescription } = require('./youtube-cta');

const DATA_PATH = path.join(ROOT, 'data', 'genre_video_packets.json');
const KATA_PATH = path.join(ROOT, 'data', 'video_kata.json');
const PROD_PATH = path.join(ROOT, 'data', 'video_production.json');
const AGENT_DIR = path.join(ROOT, 'docs', 'grok-bots', 'agents');
const WAKE_DIR = path.join(ROOT, 'docs', 'grok-bots', 'wake');
const PACKET_OUT = path.join(OUTPUT_DIR, 'video', 'packets');
const GITHUB_REPO = process.env.GITHUB_REPOSITORY || 'fireworker011/Research';
const GITHUB_REF = process.env.GROK_BOT_REF || 'cursor/video-channel-playbook-e013';

function loadCatalog() {
  const raw = JSON.parse(fs.readFileSync(DATA_PATH, 'utf-8'));
  if (!raw || !Array.isArray(raw.genres)) throw new Error('catalog missing genres');
  return raw;
}

function loadKata() {
  const raw = JSON.parse(fs.readFileSync(KATA_PATH, 'utf-8'));
  if (!raw || !Array.isArray(raw.katas)) throw new Error('kata catalog missing');
  return raw;
}

function kataById(kataCatalog, id) {
  return (kataCatalog.katas || []).find((k) => k.id === id) || null;
}

function loadProduction() {
  const raw = JSON.parse(fs.readFileSync(PROD_PATH, 'utf-8'));
  if (!raw || !raw.telop) throw new Error('production spec missing');
  return raw;
}

function agentRepoPath(genre) {
  return `affiliate-engine/docs/grok-bots/agents/${genre.id}.md`;
}

function githubRaw(repoPath) {
  return `https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_REF}/${repoPath}`;
}

function githubBlob(repoPath) {
  return `https://github.com/${GITHUB_REPO}/blob/${GITHUB_REF}/${repoPath}`;
}

function wrapLines(text, charsPerLine) {
  const lines = [];
  for (const paragraph of String(text || '').split('\n')) {
    const p = paragraph.replace(/\s+$/g, '');
    if (!p.trim()) continue;
    for (let i = 0; i < p.length; i += charsPerLine) {
      lines.push(p.slice(i, i + charsPerLine));
    }
  }
  return lines;
}

function telopCues(spoken, prod) {
  const cta = PROFILE_CTA;
  let body = String(spoken || '').trim();
  if (body.endsWith(cta)) body = body.slice(0, -cta.length).trim();
  const chars = prod.chars_per_line || 16;
  const lines = wrapLines(body, chars);
  const silent = prod.silent_head_sec;
  const perPair = prod.sec_per_two_lines;
  const ctaSec = prod.cta_last_sec;
  const clipSec = prod.imagine_clip_sec;
  const pairs = [];
  for (let i = 0; i < lines.length; i += prod.max_lines_on_screen) {
    pairs.push(lines.slice(i, i + prod.max_lines_on_screen));
  }
  if (!pairs.length) pairs.push(['']);
  const minDur = 15;
  let pairSec = perPair;
  const rawDur = silent + pairs.length * pairSec + ctaSec;
  if (rawDur < minDur) {
    pairSec = (minDur - silent - ctaSec) / pairs.length;
  }
  const cues = [{ start: 0, end: silent, lines: [], note: '文字なし・映像のみ' }];
  let t = silent;
  for (const pair of pairs) {
    const end = Math.round((t + pairSec) * 10) / 10;
    cues.push({ start: t, end, lines: pair, note: '本文' });
    t = end;
  }
  let end = Math.round((t + ctaSec) * 10) / 10;
  cues.push({ start: t, end, lines: [cta], note: 'CTA' });
  if (end < minDur) {
    const extra = Math.round((minDur - end) * 10) / 10;
    const ctaCue = cues[cues.length - 1];
    const bodyCue = cues[cues.length - 2];
    if (bodyCue && bodyCue.note === '本文') {
      bodyCue.end = Math.round((bodyCue.end + extra) * 10) / 10;
      ctaCue.start = bodyCue.end;
      ctaCue.end = Math.round((ctaCue.start + ctaSec) * 10) / 10;
      end = ctaCue.end;
    } else {
      ctaCue.end = minDur;
      end = minDur;
    }
  }
  return {
    cues,
    duration_sec: end,
    clip_count: Math.max(1, Math.ceil(end / clipSec))
  };
}

function renderCueTable(timing) {
  const rows = timing.cues.map((c) => {
    const text = c.lines.length ? c.lines.join(' / ') : '（なし）';
    return `| ${c.start.toFixed(1)}–${c.end.toFixed(1)} | ${c.note} | ${text} |`;
  });
  return [
    `| 秒 | 役割 | 画面の文字 |`,
    `|---|---|---|`,
    ...rows,
    '',
    `完成尺: ${timing.duration_sec}秒 / Imagineクリップ: ${timing.clip_count}本（各5秒を接続）`
  ].join('\n');
}

function genreByName(catalog, name) {
  const key = String(name || '').trim();
  return catalog.genres.find((g) => g.genre === key || g.id === key || g.bot_name === key) || null;
}

function activePackets(genre, { includeAfter = false } = {}) {
  const packets = genre.packets || [];
  if (genre.experiment_lock && !includeAfter) {
    return packets.filter((p) => p.phase === 'experiment');
  }
  return packets;
}

function buildPacket(catalog, genre, packet, kataCatalog, prod) {
  const spoken = applyProfileCta(packet.spoken);
  const description = youtubeDescription(packet.spoken);
  const kataId = (kataCatalog && kataCatalog.packet_kata && kataCatalog.packet_kata[packet.id]) || packet.kata || '';
  const kata = kataId && kataCatalog ? kataById(kataCatalog, kataId) : null;
  const imagine = [catalog.imagine_prefix, genre.imagine_extra, kata && kata.imagine_rule, packet.imagine]
    .filter(Boolean)
    .join('\n\n');
  const timing = telopCues(spoken, prod);
  const compliance = checkContent(`${spoken}\n${description}`);
  const urls = /https?:\/\//.test(`${spoken}\n${description}\n${imagine}`);
  const reasons = [...(compliance.reasons || [])];
  if (!compliance.ok) {
    /* keep reasons */
  }
  if (urls) reasons.push('URLが含まれている');
  if (!spoken.includes(PROFILE_CTA)) reasons.push('CTAが無い');
  if (!/#(PR|pr|広告|プロモーション|アフィリエイト)/.test(description)) reasons.push('#PRが無い');
  if (!kataId) reasons.push('kata未設定');
  if (!timing.duration_sec || timing.duration_sec < 14) reasons.push('尺が短すぎ');

  return {
    bot_name: genre.bot_name,
    genre: genre.genre,
    id: packet.id,
    link_key: packet.link_key,
    phase: packet.phase,
    kata: kataId,
    kata_name: kata ? kata.name : '',
    spoken,
    description,
    imagine,
    timing,
    output: `output/video/packets/${genre.id}/${packet.id}/reel.mp4`,
    post: false,
    ok: reasons.length === 0,
    reasons
  };
}

function renderThrow(built) {
  return [
    `宛先: ${built.bot_name}`,
    'from: manager',
    `run: ${built.phase === 'experiment' ? 'production' : built.phase === 'after_experiment' ? 'parked' : 'ready'}`,
    'post: false',
    '',
    'これだけ読んで。他のファイルを開くな。IMAGINE_THROW を Grok Imagine にそのまま投げろ。文を足すな。投稿するな。',
    '',
    '## メタ',
    `- id: ${built.id}`,
    `- kata: ${built.kata}（${built.kata_name}）`,
    `- genre: ${built.genre}`,
    `- link_key: ${built.link_key || 'なし（認知・観察）'}`,
    `- phase: ${built.phase}`,
    `- output: ${built.output}`,
    '- aspect: 9:16',
    `- duration_sec: ${built.timing.duration_sec}`,
    '- duration: レシピの完成尺（下のテロップ表）',
    `- imagine_clips: ${built.timing.clip_count} × 5秒`,
    '',
    '## テロップ表（この秒で出せ）',
    renderCueTable(built.timing),
    '',
    '## IMAGINE_THROW',
    '```',
    built.imagine,
    '```',
    '',
    '## テロップ／読み上げ',
    '```',
    built.spoken,
    '```',
    '',
    '## YouTube説明文（URLなし）',
    '```',
    built.description,
    '```',
    ''
  ].join('\n');
}

function renderKataSection(kataCatalog, genre) {
  const defaults = (kataCatalog.genre_defaults && kataCatalog.genre_defaults[genre.genre]) || {
    now: [],
    later: [],
    forbid: []
  };
  const ids = [...new Set([...(defaults.now || []), ...(defaults.later || [])])];
  const blocks = ids
    .map((id) => {
      const k = kataById(kataCatalog, id);
      if (!k) return '';
      return [
        `### ${k.id} — ${k.name}（${k.seconds}秒）`,
        `使うとき: ${k.use_when}`,
        '',
        '秒:',
        ...k.beats.map((b) => `- ${b}`),
        '',
        '台本骨格:',
        '```',
        k.spoken_skeleton,
        '```',
        '',
        `Imagine: ${k.imagine_rule}`
      ].join('\n');
    })
    .filter(Boolean)
    .join('\n\n');
  return [
    '## このジャンルの型（新レシピを足すときもこのどれか）',
    '',
    `今使う型: ${(defaults.now || []).join(', ') || 'なし'}`,
    defaults.later && defaults.later.length ? `後で: ${defaults.later.join(', ')}` : '',
    `禁止: ${(defaults.forbid || []).join(' / ')}`,
    '',
    blocks
  ]
    .filter((line) => line !== '')
    .join('\n');
}

function renderProductionSection(prod) {
  const t = prod.telop;
  return [
    '## 編集仕様（毎回これ）',
    '',
    '### キャンバス',
    `- 1080×1920、${prod.canvas.fps}fps、9:16`,
    `- 左右余白 ${prod.safe_margin_pct}%（文字は中央 ${t.max_width_px}px 幅に収める）`,
    '',
    '### テロップ位置',
    `- 領域: 画面下三分の一（${t.region}）`,
    `- 基準: 下から ${t.y_from_bottom_px}px、水平中央`,
    `- 1行 ${prod.chars_per_line}字、同時 ${prod.max_lines_on_screen}行まで`,
    `- フォント: ${t.font} ${t.size_px}px、色 ${t.color}、縁 ${t.stroke} ${t.stroke_px}px`,
    `- 行間 ${t.line_gap_px}px`,
    `- 0–${prod.silent_head_sec}秒は文字なし`,
    `- CTA「${PROFILE_CTA}」は最後の ${prod.cta_last_sec}秒だけ、同じ位置`,
    '',
    '### ナレーション',
    `- ${prod.narration.source}`,
    `- 無音ヘッドのあと本文開始。アドリブ禁止`,
    `- 画面の2行と同時にその2行を読む。次の2行に進むのは ${prod.sec_per_two_lines}秒後`,
    `- CTAも声に出す`,
    '',
    '### 編集テンポ',
    `- BGM: ${prod.edit.bgm}`,
    `- SE: ${prod.edit.se}`,
    `- カット: ${prod.edit.cut}`,
    `- プッシュイン: ${prod.edit.push_in}`,
    `- フェードイン: ${prod.edit.fade_in} / アウト: ${prod.edit.fade_out}`,
    `- 素材のつなぎ: ${prod.edit.assemble}`,
    `- Imagine 1本は ${prod.imagine_clip_sec}秒。必要本数は各レシピのテロップ表を見ろ`
  ].join('\n');
}

function renderGithubSection(genre) {
  const rel = agentRepoPath(genre);
  const raw = githubRaw(rel);
  const blob = githubBlob(rel);
  return [
    '## GitHubから読む（毎朝06:00 JST。これだけでよい）',
    '',
    'PC接続は不要。ファイルをチャットに貼らなくてよい。このチャットの過去ログより、今開いた本文が上。',
    '',
    '1. 次の raw URL をブラウザで開く',
    '2. 開いた全文に従う',
    '3. 今使うレシピを1本、編集仕様どおりに作る',
    '4. 投稿するな',
    '',
    '所定ファイル:',
    '',
    `\`${rel}\``,
    '',
    'raw（毎朝これを開け）:',
    '',
    raw,
    '',
    'GitHub表示:',
    '',
    blob
  ].join('\n');
}

function renderAgent(catalog, genre, kataCatalog, prod) {
  const experiment = (genre.packets || []).filter((p) => p.phase === 'experiment');
  const ready = (genre.packets || []).filter((p) => p.phase !== 'experiment' && p.phase !== 'after_experiment');
  const after = (genre.packets || []).filter((p) => p.phase === 'after_experiment');
  const now = genre.experiment_lock ? experiment : [...experiment, ...ready];
  const later = genre.experiment_lock ? [...ready, ...after] : after;

  const blocks = (list) =>
    list
      .map((packet) => renderThrow(buildPacket(catalog, genre, packet, kataCatalog, prod)))
      .join('\n---\n\n');

  const lockLine = genre.experiment_lock
    ? '毎朝の仕事＝今使うレシピ（実験3本）を編集仕様どおりに1本作る。after_experiment は出すな。投稿するな。型は visual_question と aruaru3 だけ。'
    : '毎朝の仕事＝今使うレシピから1本を編集仕様どおりに作る。投稿するな。チャンネル未開設でもパケットは作ってよい。公開は人間。';

  return `# ${genre.bot_name}

あなたは Grok Bot **${genre.bot_name}**。ジャンルは **${genre.genre}** だけ。

${renderGithubSection(genre)}

${lockLine}

調べられないチャンネルを成功例にするな。動画・台本はコピーするな。

## 契約（全部守れ）

- 投稿・予約・固定コメント・いいね・フォロー・DM をするな
- URL を本文・説明・コメントに書くな
- CTA は「${catalog.cta}」1回だけ
- 説明文の末尾に #PR
- 体験談を捏造するな（比較して選んだ／実際に使った、は人間承認）
- 数字を発明するな
- 絶対／必ず／100%／誰でも簡単に月○万／効果断定／元本保証を使うな
- アフィリンクをファイルに書くな
- 他ボットに直接メンションするな
- TikTok / Instagram を足すな
- ジャンルをまたぐな
- 型 id を新造するな。6つの型から選べ

ペルソナ: ${genre.persona}
担当リンクキー: ${genre.link_keys.join(' / ')}
アカウントキー: ${genre.account_key}

${renderProductionSection(prod)}

## 作れ（この順）

1. 下の「今使うレシピ」から1本選ぶ（未作成の先頭。id指定があればそれ）
2. レシピのテロップ表の秒に従え
3. IMAGINE_THROW を、クリップ本数だけ Grok Imagine に投げる（各5秒・9:16・文字なし）
4. クリップを編集仕様どおり繋ぎ、テロップを載せる
5. ナレーションはテロップ／読み上げと同一
6. \`output\` に保存。mp4 を Git にコミットするな
7. 「投稿してよい / 失敗」だけ返す

リポジトリがあるなら:

\`\`\`
cd affiliate-engine
node src/genre-video-gen.js --genre ${genre.genre}
node src/genre-video-gen.js --genre ${genre.genre} --id <id> --write
\`\`\`

${renderKataSection(kataCatalog, genre)}

## 今使うレシピ

${blocks(now) || '（なし）'}

${later.length ? `## 後で使うレシピ（今は生成するな）\n\n${blocks(later)}` : ''}
`.trim() + '\n';
}

function wakeText(genre) {
  const rel = agentRepoPath(genre);
  const raw = githubRaw(rel);
  return [
    `毎朝 06:00 JST になったら、次の URL を開き、開いた本文の全文に従え。`,
    `このチャットの過去ログより、今開いた本文が上。PC接続は不要。ファイルをここに貼らなくてよい。投稿するな。`,
    '',
    raw,
    '',
    `パス: ${rel}`,
    ''
  ].join('\n');
}

function writeAgents(catalog, kataCatalog, prod) {
  fs.mkdirSync(AGENT_DIR, { recursive: true });
  fs.mkdirSync(WAKE_DIR, { recursive: true });
  const written = [];
  for (const genre of catalog.genres) {
    const body = renderAgent(catalog, genre, kataCatalog, prod);
    const ascii = path.join(AGENT_DIR, `${genre.id}.md`);
    const named = path.join(AGENT_DIR, `${genre.bot_name}.md`);
    fs.writeFileSync(ascii, body, 'utf-8');
    fs.writeFileSync(named, body, 'utf-8');
    const wake = path.join(WAKE_DIR, `${genre.id}.txt`);
    fs.writeFileSync(wake, wakeText(genre), 'utf-8');
    written.push(path.relative(ROOT, ascii), path.relative(ROOT, named), path.relative(ROOT, wake));
  }

  const fetchLines = [
    '# 毎朝06:00 — GitHubの所定ファイルだけ読め',
    '',
    `リポジトリ: ${GITHUB_REPO}`,
    `参照ブランチ: \`${GITHUB_REF}\`（マージ後は作業ブランチに合わせる。環境変数 GROK_BOT_REF）`,
    '',
    '各 Grok Bot に、対応する `wake/<id>.txt` を **一度だけ** 貼る。以降は毎朝その raw URL を開く。チャットに md 全文を貼り直さなくてよい。',
    '',
    '各 `agents/<id>.md` に契約・編集仕様（テロップ位置・ナレーション・テンポ）・型・レシピ・テロップ表が入っている。追加ファイルは不要。',
    '',
    '| ボット | 所定ファイル | 一度だけ貼る | raw（毎朝開く） |',
    '|---|---|---|---|',
    ...catalog.genres.map((g) => {
      const rel = agentRepoPath(g);
      return `| ${g.bot_name} | \`${rel}\` | docs/grok-bots/wake/${g.id}.txt | ${githubRaw(rel)} |`;
    }),
    '',
    '投稿しない。PC接続は不要。',
    ''
  ];
  const fetchPath = path.join(ROOT, 'docs', 'grok-bots', 'FETCH.md');
  fs.writeFileSync(fetchPath, fetchLines.join('\n'), 'utf-8');
  written.push(path.relative(ROOT, fetchPath));

  const roster = [
    '# Grok Bot に今作るエージェント',
    '',
    '9体。毎朝読むファイルは ASCII 名（`agents/pet.md` など）。日本語名のファイルは同じ中身のコピー。',
    '一度だけ `docs/grok-bots/wake/<id>.txt` を貼る。以降は GitHub raw。詳細は [FETCH.md](FETCH.md)。',
    '投稿しない。',
    '',
    '| 作る名前 | 毎朝読む | 今の型 | 今生成してよいもの |',
    '|---|---|---|---|',
    ...catalog.genres.map((g) => {
      const n = activePackets(g).length;
      const nowKata = ((kataCatalog.genre_defaults || {})[g.genre] || {}).now || [];
      return `| ${g.bot_name} | docs/grok-bots/agents/${g.id}.md | ${nowKata.join(', ')} | ${g.experiment_lock ? `実験レシピ ${n}本` : `準備レシピ ${n}本（投稿禁止）`} |`;
    }),
    '',
    '作らない: 動画判定、投稿ボット、TikTok/IG専用、サクラ（Issue #54）、同人/アダアフィ。',
    ''
  ].join('\n');
  const rosterPath = path.join(ROOT, 'docs', 'grok-bots', 'CREATE.md');
  fs.writeFileSync(rosterPath, roster, 'utf-8');
  written.push(path.relative(ROOT, rosterPath));
  return written;
}

function writeOne(catalog, genre, packet, kataCatalog, prod) {
  const built = buildPacket(catalog, genre, packet, kataCatalog, prod);
  if (!built.ok) throw new Error(`${packet.id}: ${built.reasons.join('; ')}`);
  const dir = path.join(PACKET_OUT, genre.id, packet.id);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'IMAGINE_THROW.txt'), `${built.imagine}\n`, 'utf-8');
  fs.writeFileSync(path.join(dir, 'spoken.txt'), `${built.spoken}\n`, 'utf-8');
  fs.writeFileSync(path.join(dir, 'description.txt'), `${built.description}\n`, 'utf-8');
  fs.writeFileSync(path.join(dir, 'THROW.md'), renderThrow(built), 'utf-8');
  writeJSON(path.join(dir, 'manifest.json'), {
    ...built,
    imagine: built.imagine,
    created_at: new Date().toISOString()
  });
  return dir;
}

function selfTest() {
  const catalog = loadCatalog();
  const kataCatalog = loadKata();
  const prod = loadProduction();
  const links = loadConfig('links', {});
  const linkKeys = Object.keys(links).filter((k) => !k.startsWith('_'));
  if (catalog.genres.length !== 9) throw new Error(`expected 9 genres, got ${catalog.genres.length}`);
  if (kataCatalog.katas.length !== 6) throw new Error(`expected 6 katas, got ${kataCatalog.katas.length}`);

  const seenLink = new Set();
  const seenId = new Set();
  for (const genre of catalog.genres) {
    if (!genre.bot_name || !genre.genre) throw new Error('genre missing names');
    if (!kataCatalog.genre_defaults[genre.genre]) throw new Error(`no kata defaults for ${genre.genre}`);
    for (const packet of genre.packets || []) {
      if (seenId.has(packet.id)) throw new Error(`duplicate id ${packet.id}`);
      seenId.add(packet.id);
      if (packet.link_key) seenLink.add(packet.link_key);
      const built = buildPacket(catalog, genre, packet, kataCatalog, prod);
      if (!built.ok) throw new Error(`${packet.id}: ${built.reasons.join('; ')}`);
      if (built.spoken.length < 30) throw new Error(`${packet.id} too short`);
      if (!built.timing.clip_count) throw new Error(`${packet.id} missing clips`);
      if (built.timing.duration_sec < 15) throw new Error(`${packet.id} shorter than 15s`);
    }
    if (genre.experiment_lock) {
      const exp = activePackets(genre);
      if (exp.length !== 3) throw new Error(`pet experiment expected 3, got ${exp.length}`);
    }
  }

  const missingKata = [...seenId].filter((id) => !kataCatalog.packet_kata[id]);
  if (missingKata.length) throw new Error(`packets without kata: ${missingKata.join(', ')}`);
  for (const [id, kataId] of Object.entries(kataCatalog.packet_kata)) {
    if (!kataById(kataCatalog, kataId)) throw new Error(`unknown kata ${kataId} for ${id}`);
  }

  const missing = linkKeys.filter((k) => !seenLink.has(k));
  if (missing.length) throw new Error(`link keys without packet: ${missing.join(', ')}`);

  const written = writeAgents(catalog, kataCatalog, prod);
  const ascii = catalog.genres.map((g) => path.join(AGENT_DIR, `${g.id}.md`));
  for (const file of ascii) {
    const body = fs.readFileSync(file, 'utf-8');
    if (!body.includes('## 編集仕様')) throw new Error(`missing production in ${file}`);
    if (!body.includes('raw.githubusercontent.com')) throw new Error(`missing github raw in ${file}`);
    if (!body.includes('y_from_bottom') && !body.includes('下から')) throw new Error(`missing telop position in ${file}`);
  }
  if (written.length < 20) throw new Error(`expected many agent files, got ${written.length}`);
  console.log(`self-test ok: ${catalog.genres.length} agents, ${seenId.size} packets, ${kataCatalog.katas.length} katas, github fetch`);
}

function main() {
  const args = process.argv.slice(2);
  if (args.includes('--self-test')) {
    selfTest();
    return;
  }
  const catalog = loadCatalog();
  const kataCatalog = loadKata();
  const prod = loadProduction();
  if (args.includes('--write-agents')) {
    const written = writeAgents(catalog, kataCatalog, prod);
    console.log(written.join('\n'));
    return;
  }
  if (args.includes('--list-kata')) {
    for (const k of kataCatalog.katas) {
      console.log(`${k.id}\t${k.name}\t${k.seconds}\t${k.use_when}`);
    }
    return;
  }
  if (args.includes('--list')) {
    for (const g of catalog.genres) {
      const n = activePackets(g).length;
      const total = (g.packets || []).length;
      const nowKata = ((kataCatalog.genre_defaults || {})[g.genre] || {}).now || [];
      console.log(`${g.bot_name}\t${g.genre}\tkata=${nowKata.join(',')}\tnow=${n}\tall=${total}`);
    }
    return;
  }

  const gi = args.indexOf('--genre');
  if (gi === -1) {
    console.error('usage: --list | --list-kata | --genre NAME [--id ID] [--write] [--all] | --write-agents | --self-test');
    process.exit(2);
  }
  const genre = genreByName(catalog, args[gi + 1]);
  if (!genre) {
    console.error(`unknown genre: ${args[gi + 1]}`);
    process.exit(1);
  }
  const idIndex = args.indexOf('--id');
  const includeAfter = args.includes('--all');
  let packets = activePackets(genre, { includeAfter });
  if (idIndex !== -1) {
    const id = args[idIndex + 1];
    packets = (genre.packets || []).filter((p) => p.id === id);
    if (!packets.length) {
      console.error(`unknown id: ${id}`);
      process.exit(1);
    }
  }
  for (const packet of packets) {
    const built = buildPacket(catalog, genre, packet, kataCatalog, prod);
    if (!built.ok) {
      console.error(`${packet.id}: ${built.reasons.join('; ')}`);
      process.exit(1);
    }
    if (args.includes('--write')) {
      const dir = writeOne(catalog, genre, packet, kataCatalog, prod);
      console.log(`wrote ${dir}`);
    } else {
      process.stdout.write(renderThrow(built));
      process.stdout.write('\n');
    }
  }
}

main();
