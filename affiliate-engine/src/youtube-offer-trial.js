#!/usr/bin/env node
'use strict';

/**
 * FUNNEL_WEAK の次の一手（人間が 2026-09-09 に A を選んだ）。
 * カメラ以外を 1 本だけ。着地はペット保険の資料請求（申込型・無料）。
 *
 * やること: 台本を検品して出す。投稿しない。量産しない。ジャンルを変えない。
 * 体験談は書かない。「一番安い」「必ず入る」は書かない。特定の保険会社名は出さない。
 *
 *   node src/youtube-offer-trial.js
 *   node src/youtube-offer-trial.js --self-test
 */

const { checkContent, validateTemplate } = require('./compliance');
const { PROFILE_CTA, applyProfileCta, youtubeDescription } = require('./youtube-cta');

const TRIAL = {
  id: 'pet_offer_trial_1',
  decided: '2026-09-09',
  choice: 'A',
  offer: 'ペット保険の資料請求',
  link_key: 'ペット_保険',
  title: '病院代の前に見る3つ',
  spoken: [
    '動物病院の会計、桁が違うことがある。',
    '',
    '入る・入らないの前に、この3つだけ見る。',
    '1. 補償割合。何割戻るか',
    '2. 対象外。予防や既往は出ないことが多い',
    '3. 待機期間と、入れる年齢',
    '',
    '資料請求は無料。パンフレットを取り寄せてから決めてよい。'
  ].join('\n'),
  why: [
    'A8公開のペット欄（2026-08-10）は購入型が多い。Furboは購入10%、本体はセール時でも数千円〜通常数万円。',
    '申込型でチャンネルの癒しShortsと衝突しにくいのは、ペット保険の資料請求（無料・特定社を推さない）。',
    '火葬の電話問合せは成果地点は浅いが、癒しチャンネルの着地には使わない。',
    'フード初回購入はカメラより安いが購入型。今回は申込型だけを1本試す。'
  ]
};

function spokenText() {
  return TRIAL.spoken;
}

function asTemplate() {
  return {
    id: TRIAL.id,
    genre: 'ペット',
    content: spokenText(),
    emoji: '📋',
    engagement_prediction: 'medium',
    cta_type: 'direct',
    link_key: TRIAL.link_key
  };
}

function inspect() {
  const content = spokenText();
  const structural = validateTemplate(
    { id: TRIAL.id, genre: 'ペット', content },
    { genres: ['ペット'] }
  );
  if (!structural.ok) {
    return { ok: false, reasons: structural.reasons };
  }
  const spoken = applyProfileCta(content);
  const spokenCheck = checkContent(spoken);
  if (!spokenCheck.ok) return { ok: false, reasons: spokenCheck.reasons };
  let description;
  try {
    description = youtubeDescription(content);
  } catch (err) {
    return { ok: false, reasons: [err.message] };
  }
  const descCheck = checkContent(description);
  if (!descCheck.ok) return { ok: false, reasons: descCheck.reasons };
  return { ok: true, spoken: spokenCheck.text, description: descCheck.text, reasons: [] };
}

function renderMarkdown(inspected) {
  const lines = [
    `# 案件試験 1本 — ${TRIAL.offer}`,
    '',
    `人間の決定: ${TRIAL.decided} に **${TRIAL.choice}**（安い／申込型を1本）。カメラ動画は増やさない。量産しない。媒体は足さない。`,
    '',
    'チャンネル: YouTube `@pet_story_select`',
    `台本ID: \`${TRIAL.id}\``,
    `着地キー: \`${TRIAL.link_key}\`（URLはGitに置かない。プロフィールだけ）`,
    `タイトル案: ${TRIAL.title}`,
    '',
    '## なぜこれか',
    ''
  ];
  for (const w of TRIAL.why) lines.push(`- ${w}`);
  lines.push('');
  lines.push('報酬額・EPC・確定率はA8管理画面を見るまで書かない。');
  lines.push('');
  lines.push('## 人間が投稿前にやること（この順）');
  lines.push('');
  lines.push('1. A8で「ペット保険」「資料請求」を検索する。成果地点が**資料請求**のプログラムを **1つだけ** 提携する。特定社を「一番おすすめ」と書いている案件は避ける（比較サイトの一括請求型が安全）。');
  lines.push('2. チャンネル概要の外部リンクを、その資料請求URLに差し替える。**この試験中はカメラ用リンクと並べない**（クリックの着地が混ざる）。概要のPR表記はそのまま。');
  lines.push('3. 下の台本で Shorts を **1本だけ** 撮る。映像の型（癒し）は変えてよいが、新しいジャンルにはしない。末尾で1回だけ「詳しくはプロフィールのリンク（PR）」。');
  lines.push('4. 説明欄は下のブロックをそのまま。固定コメントにURLは置かない。既存32本は触らない。');
  lines.push('5. `data/video_cash_log.csv` にその日の1行。note は `offer-trial-1 insurance`。数字が無い日は空欄のままにしない。');
  lines.push('6. 同じ台本で2本目を出さない。判定はCSV。成果が出るまで案件を増やさない。');
  lines.push('');
  lines.push('映像の型は変えない必要はない（これは癒し3本の再掲ではない）。**本数だけ1本。**');
  lines.push('');
  lines.push('テロップ／読み上げ:');
  lines.push('```');
  lines.push(inspected.spoken);
  lines.push('```');
  lines.push('');
  lines.push('YouTube説明文（URLなし）:');
  lines.push('```');
  lines.push(inspected.description);
  lines.push('```');
  lines.push('');
  lines.push('生成: `npm run youtube:offer1`');
  lines.push('');
  return `${lines.join('\n')}\n`;
}

function assert(cond, label) {
  if (!cond) throw new Error(label);
}

function runSelfTest() {
  const r = inspect();
  assert(r.ok, `inspect failed: ${(r.reasons || []).join(', ')}`);
  assert(r.spoken.includes(PROFILE_CTA), 'spoken missing profile CTA');
  assert(r.description.includes('#PR') || r.description.includes('#pr'), 'description missing #PR');
  assert(!/https?:\/\//.test(r.description), 'description has URL');
  assert(!/\{\{/.test(r.spoken), 'placeholder in spoken');
  assert(!/うちで比較|実際に入った|一番おすすめ|必ず入/.test(r.spoken + r.description), 'banned testimonial/superlative');
  assert(!/Furbo|見守りカメラ/.test(r.spoken), 'camera offer leaked');
  assert(asTemplate().link_key === 'ペット_保険', 'link_key');
  const md = renderMarkdown(r);
  assert(/offer-trial-1 insurance/.test(md), 'csv note missing');
  console.log('self-test ok');
}

function main() {
  const r = inspect();
  if (!r.ok) {
    console.error(`検品で落ちた: ${r.reasons.join(', ')}`);
    process.exit(1);
  }
  process.stdout.write(renderMarkdown(r));
}

module.exports = { TRIAL, inspect, renderMarkdown, asTemplate };

if (require.main === module) {
  if (process.argv.includes('--self-test')) {
    try {
      runSelfTest();
    } catch (err) {
      console.error(`self-test failed: ${err.message}`);
      process.exit(1);
    }
  } else {
    main();
  }
}
