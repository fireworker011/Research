'use strict';

const { categoryById, addDays, dateJst } = require('./util');
const { HUMAN_PLACEHOLDER, checkDraft } = require('./compliance');

const INTENTS = Object.freeze([
  'contract_offer',
  'ask_experience',
  'ask_ai',
  'deadline',
  'revision',
  'price',
  'external_contact',
  'prepay_request',
  'delivery_ack',
  'thanks',
  'unknown'
]);

const INTENT_RULES = [
  ['external_contact', /(LINE|ライン|Discord|チャットワーク|Slack|電話|Zoom|ミーティング)[^。\n]{0,12}(で|に|へ|を)(連絡|移動|やり取り|お願い|追加|お話)/],
  ['prepay_request', /(仮払い(の)?前|先に[^。\n]{0,8}(作業|着手|書い|作っ|試し)|(無償|無料)(で)?(テスト|トライアル|サンプル)|(まず|試しに)[^。\n]{0,6}(作っ|書い)て|テスト(で|として)[^。\n]{0,6}(書い|作っ|やっ)て)/],
  ['revision', /(修正|直し|変更|作り直|リテイク|ここを|以下の点|再提出)/],
  ['deadline', /(納期|いつまで|期限|何日|スケジュール|急ぎ|至急)/],
  ['price', /(金額|単価|報酬|値下げ|お安く|予算|円で)/],
  ['ask_ai', /(AI|ＡＩ|ChatGPT|生成)/],
  ['ask_experience', /(経験|実績|ポートフォリオ|過去の|作品|できますか|得意)/],
  ['contract_offer', /(契約|お願いしたい|依頼したい|採用|発注|進めましょう|決定)/],
  ['delivery_ack', /(検収|確認しました|受け取り|納品ありがとう|問題ありません|OKです)/],
  ['thanks', /(ありがとう|よろしくお願い|承知)/]
];

function classifyAll(text) {
  const t = String(text || '');
  const hits = INTENT_RULES.filter(([, re]) => re.test(t)).map(([intent]) => intent);
  return hits.length ? hits : ['unknown'];
}

function classify(text) {
  return classifyAll(text)[0];
}

const SECONDARY_OK = new Set(['prepay_request', 'external_contact', 'deadline', 'ask_ai', 'ask_experience']);

function stripHead(text) {
  return String(text || '').replace(/^ご連絡ありがとうございます。\n/, '');
}

function replyFor(intent, { job, facts, capability, now }) {
  const category = categoryById(capability, job?.category);
  const pub = facts?.public_profile_facts || {};
  const eta = addDays(dateJst(now), category ? category.turnaround_days : 2);
  const head = 'ご連絡ありがとうございます。';
  switch (intent) {
    case 'contract_offer':
      return `${head}\n条件を確認しました。契約と仮払いの確定後に着手し、初稿は ${eta} を目安にお送りします。修正は1回まで無償で対応します。\n作業には生成AIを補助的に使い、最終確認は私が行います。条件があればお知らせください。`;
    case 'ask_experience':
      return `${head}\n${Number(pub.deliveries_completed || 0) > 0 ? `クラウドワークスでの完成納品は ${pub.deliveries_completed} 件です。` : 'クラウドワークスでの完成納品はまだありません。無い実績は書きません。'}\n代わりに、募集文のテーマで短いサンプルを1つ作成してお送りできます。ご希望があればお知らせください。`;
    case 'ask_ai':
      return `${head}\n${facts?.ai_policy?.use_ai === false ? '生成AIは使用しません。' : '作業には生成AIを補助的に使い、構成・事実確認・最終修正は私が行います。'}\nAI利用に条件（使用不可・申告必須・ツール指定）があれば、その条件に従います。`;
    case 'deadline':
      return `${head}\n初稿は ${eta} までにお送りできます。ご希望の納期があればお知らせください。難しい場合は事前にご相談します。`;
    case 'revision':
      return `${head}\n修正内容を確認しました。次の点を反映します。\n${HUMAN_PLACEHOLDER}（クライアントの修正点を箇条書きで写す）\n反映版は ${eta} までにお送りします。`;
    case 'price':
      return `${head}\n金額は募集に記載の条件で問題ありません。${HUMAN_PLACEHOLDER}（変更提案があれば人間が判断して書く。掲載条件を下回る値下げは受けない）`;
    case 'external_contact':
      return `${head}\n恐れ入りますが、やり取りはクラウドワークスのメッセージ内でお願いしています（規約に沿った運用のためです）。ファイルの受け渡しもこちらで対応できます。`;
    case 'prepay_request':
      return `${head}\n恐れ入りますが、作業は契約と仮払いの確定後に着手しています（クラウドワークスの規約に沿った運用のためです）。テストが必要な場合は、テスト分も契約に含めていただければすぐ着手します。`;
    case 'delivery_ack':
      return `${head}\nご確認ありがとうございます。問題なければ検収をお願いします。今後も同種の業務があればお声がけください。`;
    case 'thanks':
      return `${head}\nこちらこそありがとうございます。進捗や確認事項があれば、このメッセージでお知らせします。引き続きよろしくお願いいたします。`;
    case 'unknown':
      return `${head}\n${HUMAN_PLACEHOLDER}（定型に当たらない。人間が判断して書く。実績の発明・外部連絡・仮払い前作業は受けない）`;
    default: {
      const _never = intent;
      throw new Error(`unknown intent: ${_never}`);
    }
  }
}

function draftReply(messageText, ctx) {
  const intents = classifyAll(messageText);
  const intent = intents[0];
  const secondary = intents.slice(1).find((i) => SECONDARY_OK.has(i) && i !== intent) || null;
  let text = replyFor(intent, ctx);
  if (secondary) text = `${text}\n\n${stripHead(replyFor(secondary, ctx))}`;
  const check = checkDraft(text, { facts: ctx.facts, kind: 'reply', maxChars: 1200 });
  return { intent, intents, text, check };
}

module.exports = { INTENTS, classify, classifyAll, replyFor, draftReply };
