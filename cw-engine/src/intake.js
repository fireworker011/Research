'use strict';

const { stripHtml } = require('./util');

const PUBLIC_JOB_URL = 'https://crowdworks.jp/public/jobs/';

const FLAG_RULES = {
  closed: /(募集(は|を)?終了|募集終了|応募期限を過ぎ|このお仕事は終了)/,
  on_camera: /(顔出し|ご出演|出演していただ|モデル(を)?募集|撮影を担当|撮影して(いただ|もら)|ご自身で撮影|撮影から(編集|お願い)|自撮り)/,
  ai_forbidden: /((AI|ＡＩ|ChatGPT|生成AI|生成系AI)[^。\n]{0,14}(禁止|不可|NG|使用しない|使わない|お断り|認めません))|((禁止|不可|NG)[^。\n]{0,8}(AI|ChatGPT))/i,
  ai_disclose_required: /(AI|ＡＩ|ChatGPT)[^。\n]{0,14}(申告|明記|お知らせ|申し出|事前に)/i,
  review_posting: /((口コミ|クチコミ|レビュー|星|★)[^。\n]{0,8}(投稿|書き込|登録|して(ください|頂|いただ)))|(Amazon[^。\n]{0,10}レビュー)|(Google[^。\n]{0,10}(口コミ|クチコミ))|食べログ|(サクラ|やらせ)/,
  seo_manipulation: /(被リンク|順位操作|検索順位を(上げ|操作)|サジェスト(汚染|対策))/,
  ranking_manipulation: /ランキング[^。\n]{0,8}(投票|操作|上げ)/,
  affiliate_registration: /(アフィリエイト(登録|案件)|メルマガ(に)?登録|(登録|インストール|申込|申し込み)[^。\n]{0,12}(スクショ|スクリーンショット|完了で報酬|していただくだけ))/,
  account_work: /(アカウント(作成|開設|貸与|譲渡|運用)代行|(SNS|LINE)?アカウント[^。\n]{0,6}(作成|開設)して(ください|いただ)|代理(ログイン|登録)|ログイン(して|情報を)(いただ|お渡し))/,
  mlm: /(MLM|ネットワークビジネス|マルチ商法|紹介した人数|権利収入)/,
  academic: /(レポート|論文|卒論|課題|宿題)[^。\n]{0,6}(代行|代筆)/,
  adult: /(アダルト|R18|R-18|18禁|成人向け|エロ|風俗)/,
  personal_data: /(個人情報|名簿|電話番号|メールアドレス|住所)[^。\n]{0,12}(入力|収集|リスト|抜き出|集め)/,
  external_contact_first: /(LINE|ライン|Discord|チャットワーク|Slack)[^。\n]{0,10}(で連絡|に移動|でやり取り|に登録|を追加)/,
  prepay_risk: /(仮払い前|先に[^。\n]{0,8}(作業|着手|書い|作っ)|(無償|無料)(で)?(テスト|トライアル|サンプル)|テスト(は)?無償|(採用前|契約前)に(作業|作成|提出))/,
  needs_portfolio: /(((ポートフォリオ|実績|作品|制作物)[^。\n]{0,8}(必須|必ず|ご提出|添付|お送り|拝見))|経験者(のみ|限定|優遇のみ)|経験\s*\d+\s*年以上|実績(の)?ある方|経験(が)?必須|即戦力)/,
  portfolio_optional: /(ポートフォリオ|実績)[^。\n]{0,6}(あれば|任意|もしあれば|お持ちであれば)/,
  materials_provided: /((素材|資料|台本|原稿|キーワード|構成案|元データ|参考(資料|動画)|音声(データ)?|テンプレ(ート)?|マニュアル)[^。\n]{0,14}(支給|提供|お渡し|共有|ご用意|用意して|あります|はこちら|お送り))|撮影済み/,
  unexperienced_ok: /(未経験(OK|ＯＫ|可|歓迎|でも|の方も)|初心者(OK|ＯＫ|歓迎|可)|はじめて(の方)?(OK|ＯＫ|歓迎)|経験不問|スキル不要|簡単な作業)/,
  continuous: /(継続|長期|定期的|月\s*\d+\s*本)/,
  school_excluded: /スクール(受講中|生)は(対象外|ご遠慮)/
};

const ASK_HEAD = /(応募時|応募の際|ご応募(いただく|の)際|応募文|応募メッセージ)[^。\n]{0,14}(記載|記入|お書き|ご回答|教えて|お知らせ|明記)/;
const ASK_LINE = /^\s*(?:[・\-●■◆□▪︎※◎○]|[①-⑳]|\d{1,2}[.)．、]|[（(]\d{1,2}[)）])\s*(.+?)\s*$/;

function detectFlags(text) {
  const t = String(text || '');
  const flags = {};
  for (const [k, re] of Object.entries(FLAG_RULES)) flags[k] = re.test(t);
  if (flags.portfolio_optional && !/必須|必ず/.test(t)) flags.needs_portfolio = false;
  return flags;
}

function detectCategory(text, capability) {
  const t = String(text || '');
  let best = null;
  for (const cat of capability?.categories || []) {
    let score = 0;
    for (const kw of cat.keywords || []) {
      const hits = t.split(kw).length - 1;
      score += hits;
    }
    if (score === 0) continue;
    if (!best || score > best.score || (score === best.score && cat.priority > best.priority)) {
      best = { id: cat.id, score, priority: cat.priority };
    }
  }
  return best ? best.id : 'unknown';
}

function extractAsks(text) {
  const lines = String(text || '').split(/\r?\n/);
  const asks = [];
  for (let i = 0; i < lines.length; i++) {
    if (!ASK_HEAD.test(lines[i])) continue;
    for (let j = i + 1; j < lines.length && asks.length < 12; j++) {
      const line = lines[j];
      if (!line.trim()) {
        if (asks.length) break;
        continue;
      }
      const m = line.match(ASK_LINE);
      if (m) asks.push(m[1].replace(/[（(].*?(任意|あれば).*?[)）]/g, (s) => s).trim());
      else if (asks.length) break;
    }
    if (asks.length) break;
  }
  return [...new Set(asks)];
}

function extractDate(text, labelRe) {
  const m = String(text || '').match(new RegExp(`${labelRe.source}[^0-9]{0,12}(\\d{4})[/年.\\-](\\d{1,2})[/月.\\-](\\d{1,2})`));
  if (!m) return null;
  return `${m[1]}-${String(m[2]).padStart(2, '0')}-${String(m[3]).padStart(2, '0')}`;
}

function extractCount(text, labelRe) {
  const m = String(text || '').match(new RegExp(`${labelRe.source}\\s*(\\d+)\\s*人`));
  return m ? Number(m[1]) : null;
}

function extractPublicPrice(text) {
  const nums = [];
  for (const m of String(text || '').matchAll(/([\d,]{1,9})\s*円/g)) {
    const n = Number(m[1].replace(/,/g, ''));
    if (Number.isFinite(n) && n > 0) nums.push(n);
  }
  return nums.length ? Math.max(...nums) : null;
}

function extractCharSpec(text) {
  const m = String(text || '').match(/(\d{3,5})\s*[〜~～\-]\s*(\d{3,5})\s*(文字|字)/) || String(text || '').match(/(\d{3,5})\s*(文字|字)(程度|前後|以上)/);
  if (!m) return null;
  const lo = Number(m[1]);
  const hi = m[2] && /^\d+$/.test(m[2]) ? Number(m[2]) : Math.round(lo * 1.3);
  return [lo, hi];
}

function firstLine(text) {
  const line = String(text || '')
    .split(/\r?\n/)
    .map((s) => s.trim())
    .find((s) => s.length >= 4);
  return (line || '').slice(0, 80);
}

function parseJobText(id, text, capability, overrides = {}) {
  const clean = String(text || '').replace(/\r/g, '');
  const flags = detectFlags(clean);
  const category = overrides.category || detectCategory(clean, capability);
  const handle = capability?.account || 'fireworker12';
  const already = overrides.applied === 'yes' || (clean.includes(handle) && /応募した人|応募者/.test(clean));
  return {
    id: String(id).trim(),
    title: overrides.title || firstLine(clean),
    category,
    flags: { ...flags, already_applied: already },
    asks: extractAsks(clean),
    deadline: extractDate(clean, /(?:応募期限|納期|締切|締め切り)/) || null,
    applicants: extractCount(clean, /応募した人/),
    contracted: extractCount(clean, /契約した人/),
    openings: extractCount(clean, /募集人数/),
    public_price_yen: extractPublicPrice(clean),
    char_spec: extractCharSpec(clean),
    text_excerpt: clean.slice(0, 600),
    text_chars: clean.length
  };
}

async function fetchPublicJob(id, { fetchImpl = fetch, timeoutMs = 15000 } = {}) {
  const url = `${PUBLIC_JOB_URL}${encodeURIComponent(String(id))}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetchImpl(url, {
      headers: { 'user-agent': 'cw-engine/1.0 (read-only public job page; no login; no auto-apply)' },
      signal: controller.signal
    });
    if (!res.ok) return { ok: false, reason: `http_${res.status}` };
    const html = await res.text();
    if (/ログイン|login/i.test(html.slice(0, 2000)) && !/仕事の詳細|募集/.test(html)) return { ok: false, reason: 'login_wall' };
    const titleMatch = html.match(/<title>([\s\S]*?)<\/title>/i);
    const text = stripHtml(html);
    if (text.length < 200) return { ok: false, reason: 'too_short' };
    return { ok: true, text, title: titleMatch ? stripHtml(titleMatch[1]).slice(0, 80) : null };
  } catch (err) {
    return { ok: false, reason: err.name === 'AbortError' ? 'timeout' : `fetch_error` };
  } finally {
    clearTimeout(timer);
  }
}

module.exports = {
  PUBLIC_JOB_URL,
  FLAG_RULES,
  detectFlags,
  detectCategory,
  extractAsks,
  extractPublicPrice,
  extractCharSpec,
  parseJobText,
  fetchPublicJob
};
