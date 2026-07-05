#!/usr/bin/env node
'use strict';

/**
 * インサイト草案の反映
 * data/proposed_templates.json（insight.js の出力・レビュー済み前提）を
 * data/seed_templates.json に統合し、スケジュールを再生成する。
 *
 * 使用方法:
 *   node src/apply-proposals.js            # 統合 + スケジュール再生成
 *   node src/apply-proposals.js --prune 5  # ついでに views 実測ワースト5テンプレを引退させる
 *   node src/apply-proposals.js --auto --prune 3 --cap 36
 *     --auto: 草案ゼロでもエラー終了しない（毎日の自動実行用）
 *     --cap N: ジャンルごとのテンプレ総数を N 本に抑える（超過分は古い価値提供テンプレから引退。
 *              リンク付きテンプレは対象外。テンプレの肥大化と型の陳腐化を防ぐ）
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { ROOT, OUTPUT_DIR, readJSON, writeJSON } = require('./util');

const SEED_PATH = path.join(ROOT, 'data', 'seed_templates.json');
const PROPOSED_PATH = path.join(ROOT, 'data', 'proposed_templates.json');

function main() {
  const seed = readJSON(SEED_PATH);
  const proposed = readJSON(PROPOSED_PATH) || {};
  if (!Array.isArray(proposed.posting_templates)) proposed.posting_templates = [];

  if (!seed) {
    console.error('❌ data/seed_templates.json が読めません');
    process.exit(1);
  }
  const isAuto = process.argv.includes('--auto');
  if (proposed.posting_templates.length === 0) {
    if (isAuto) {
      console.log('（草案なし: 統合はスキップしスケジュール再生成のみ実行）');
    } else {
      console.error('❌ data/proposed_templates.json に草案がありません（先に node src/insight.js を実行）');
      process.exit(1);
    }
  }

  const existingIds = new Set(seed.posting_templates.map((t) => t.id));
  const existingContents = new Set(seed.posting_templates.map((t) => t.content));

  let added = 0;
  for (const t of proposed.posting_templates) {
    if (existingIds.has(t.id) || existingContents.has(t.content)) continue;
    seed.posting_templates.push(t);
    existingIds.add(t.id);
    added++;
  }
  console.log(`✓ 草案 ${added} 本を seed に統合（重複 ${proposed.posting_templates.length - added} 本はスキップ）`);

  // --prune N: 実測 views ワースト N 本を引退（リンク投稿は温存し、価値提供のみ対象）
  const pruneIdx = process.argv.indexOf('--prune');
  if (pruneIdx !== -1) {
    const n = parseInt(process.argv[pruneIdx + 1] || '0', 10);
    const topPosts = readJSON(path.join(OUTPUT_DIR, 'top_posts.json'), []);
    if (n > 0 && topPosts.length > 0) {
      const viewsByText = new Map(topPosts.map((p) => [p.text, p.views || 0]));
      const candidates = seed.posting_templates
        .filter((t) => !String(t.content).includes('{{AFFILIATE_LINK}}'))
        .map((t) => ({ t, views: [...viewsByText.entries()].find(([text]) => text && text.startsWith(String(t.content).slice(0, 40)))?.[1] }))
        .filter((c) => c.views !== undefined)
        .sort((a, b) => a.views - b.views)
        .slice(0, n);
      const retireIds = new Set(candidates.map((c) => c.t.id));
      seed.posting_templates = seed.posting_templates.filter((t) => !retireIds.has(t.id));
      console.log(`✓ 実測ワースト ${retireIds.size} 本を引退: ${[...retireIds].join(', ')}`);
    } else {
      console.log('  （--prune: 実測データ不足のためスキップ）');
    }
  }

  // --cap N: ジャンルごとにテンプレ総数を制限（古い価値提供テンプレから引退。リンク付きは温存）
  const capIdx = process.argv.indexOf('--cap');
  if (capIdx !== -1) {
    const cap = parseInt(process.argv[capIdx + 1] || '0', 10);
    if (cap > 0) {
      const countByGenre = {};
      for (const t of seed.posting_templates) {
        countByGenre[t.genre] = (countByGenre[t.genre] || 0) + 1;
      }
      const retired = [];
      for (const [genre, count] of Object.entries(countByGenre)) {
        let excess = count - cap;
        if (excess <= 0) continue;
        // 配列先頭 = 古いテンプレから順に引退候補にする
        for (const t of seed.posting_templates) {
          if (excess <= 0) break;
          if (t.genre !== genre) continue;
          if (String(t.content).includes('{{AFFILIATE_LINK}}')) continue;
          retired.push(t.id);
          excess--;
        }
      }
      if (retired.length > 0) {
        const retiredSet = new Set(retired);
        seed.posting_templates = seed.posting_templates.filter((t) => !retiredSet.has(t.id));
        console.log(`✓ ジャンル上限 ${cap} 本超過分 ${retired.length} 本を引退: ${retired.join(', ')}`);
      }
    }
  }

  writeJSON(SEED_PATH, seed);
  console.log(`✓ seed_templates.json 更新（計 ${seed.posting_templates.length} 本）`);

  // 反映済みの草案ファイルは空にして二重適用を防ぐ
  writeJSON(PROPOSED_PATH, { applied_at: new Date().toISOString(), posting_templates: [] });

  console.log('\n📋 スケジュール再生成中...');
  const result = spawnSync('node', [path.join(__dirname, 'strategy-engine.js'), '--from-file', SEED_PATH], {
    stdio: 'inherit',
    cwd: ROOT
  });
  process.exit(result.status || 0);
}

main();
