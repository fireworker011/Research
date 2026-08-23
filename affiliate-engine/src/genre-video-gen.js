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
const AGENT_DIR = path.join(ROOT, 'docs', 'grok-bots', 'agents');
const PACKET_OUT = path.join(OUTPUT_DIR, 'video', 'packets');

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

function buildPacket(catalog, genre, packet, kataCatalog) {
  const spoken = applyProfileCta(packet.spoken);
  const description = youtubeDescription(packet.spoken);
  const kataId = (kataCatalog && kataCatalog.packet_kata && kataCatalog.packet_kata[packet.id]) || packet.kata || '';
  const kata = kataId && kataCatalog ? kataById(kataCatalog, kataId) : null;
  const imagine = [catalog.imagine_prefix, genre.imagine_extra, kata && kata.imagine_rule, packet.imagine]
    .filter(Boolean)
    .join('\n\n');
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
    '- duration: 5',
    '- aspect: 9:16',
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

function renderAgent(catalog, genre, kataCatalog) {
  const experiment = (genre.packets || []).filter((p) => p.phase === 'experiment');
  const ready = (genre.packets || []).filter((p) => p.phase !== 'experiment' && p.phase !== 'after_experiment');
  const after = (genre.packets || []).filter((p) => p.phase === 'after_experiment');
  const now = genre.experiment_lock ? experiment : [...experiment, ...ready];
  const later = genre.experiment_lock ? [...ready, ...after] : after;

  const blocks = (list) =>
    list
      .map((packet) => renderThrow(buildPacket(catalog, genre, packet, kataCatalog)))
      .join('\n---\n\n');

  const lockLine = genre.experiment_lock
    ? '「これだけ読んで」＝今使うレシピ（実験3本）を生成する。after_experiment は出すな。投稿するな。型は visual_question と aruaru3 だけ。'
    : '「これだけ読んで」＝今使うレシピから1本生成する（id指定があればそれ）。投稿するな。チャンネルが未開設でもパケットは作ってよい。公開は人間。新テーマは下の型のどれかで書け。';

  return `# ${genre.bot_name}

あなたは Grok Bot **${genre.bot_name}**。ジャンルは **${genre.genre}** だけ。
人間が「これだけ読んで」と言ったら、**このファイルだけ**を読め。他のマニュアル・他ジャンル・insight.js を開くな。

${lockLine}

市場リサーチの要約はファイル末尾の型に入っている。調べられないチャンネルを成功例にするな。動画・台本はコピーするな。

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

## これだけ読んで／作れと言われたら（この順）

1. 下の「今使うレシピ」から1本選ぶ（人間が id を指定したらそれ）
2. レシピの kata を守れ。秒の骨格を崩すな
3. IMAGINE_THROW を Grok Imagine にそのまま投げる（5秒 / 9:16 / 文字なし）
4. 動画を output に保存する。リポジトリへ mp4 をコミットするな
5. テロップと説明文はレシピのまま。文を足すな
6. 「投稿してよい / 失敗」だけ返す。公式アプリで上げるのは人間

リポジトリがあるなら:

\`\`\`
cd affiliate-engine
node src/genre-video-gen.js --genre ${genre.genre}
node src/genre-video-gen.js --genre ${genre.genre} --id <id> --write
node src/genre-video-gen.js --list-kata
\`\`\`

${renderKataSection(kataCatalog, genre)}

## 今使うレシピ

${blocks(now) || '（なし）'}

${later.length ? `## 後で使うレシピ（今は生成するな）\n\n${blocks(later)}` : ''}
`.trim() + '\n';
}

function writeAgents(catalog, kataCatalog) {
  fs.mkdirSync(AGENT_DIR, { recursive: true });
  const written = [];
  for (const genre of catalog.genres) {
    const file = path.join(AGENT_DIR, `${genre.bot_name}.md`);
    fs.writeFileSync(file, renderAgent(catalog, genre, kataCatalog), 'utf-8');
    written.push(path.relative(ROOT, file));
  }
  const roster = [
    '# Grok Bot に今作るエージェント',
    '',
    '9体。名前は下のまま。最初のメッセージに対応ファイルを貼り、続けて「これだけ読んで」と書く。',
    '投稿しない。リンク22本分のボットは作らない。1ジャンル1体が、そのジャンルの案件キー分のレシピと型を持つ。',
    '市場と型の本文: docs/grok-bots/MARKET_AND_KATA.md',
    '',
    '| 作る名前 | 貼るファイル | 今の型 | 今生成してよいもの |',
    '|---|---|---|---|',
    ...catalog.genres.map((g) => {
      const n = activePackets(g).length;
      const nowKata = ((kataCatalog.genre_defaults || {})[g.genre] || {}).now || [];
      return `| ${g.bot_name} | docs/grok-bots/agents/${g.bot_name}.md | ${nowKata.join(', ')} | ${g.experiment_lock ? `実験レシピ ${n}本` : `準備レシピ ${n}本（投稿禁止）`} |`;
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

function writeOne(catalog, genre, packet, kataCatalog) {
  const built = buildPacket(catalog, genre, packet, kataCatalog);
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
      const built = buildPacket(catalog, genre, packet, kataCatalog);
      if (!built.ok) throw new Error(`${packet.id}: ${built.reasons.join('; ')}`);
      if (built.spoken.length < 30) throw new Error(`${packet.id} too short`);
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

  const written = writeAgents(catalog, kataCatalog);
  if (written.length < 10) throw new Error('agent files not written');
  console.log(`self-test ok: ${catalog.genres.length} agents, ${seenId.size} packets, ${kataCatalog.katas.length} katas`);
}

function main() {
  const args = process.argv.slice(2);
  if (args.includes('--self-test')) {
    selfTest();
    return;
  }
  const catalog = loadCatalog();
  const kataCatalog = loadKata();
  if (args.includes('--write-agents')) {
    const written = writeAgents(catalog, kataCatalog);
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
    const built = buildPacket(catalog, genre, packet, kataCatalog);
    if (!built.ok) {
      console.error(`${packet.id}: ${built.reasons.join('; ')}`);
      process.exit(1);
    }
    if (args.includes('--write')) {
      const dir = writeOne(catalog, genre, packet, kataCatalog);
      console.log(`wrote ${dir}`);
    } else {
      process.stdout.write(renderThrow(built));
      process.stdout.write('\n');
    }
  }
}

main();
