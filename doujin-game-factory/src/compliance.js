"use strict";

const MINOR_PATTERNS = [
  /ロリ/i,
  /ショタ/i,
  /js\b/i,
  /jc\b/i,
  /jk\b/i,
  /小学生/,
  /中学生/,
  /高校生/,
  /園児/,
  /幼女/,
  /少年(?!兵)/,
  /少女/,
  /\bchild\b/i,
  /\bloli\b/i,
  /\bshota\b/i,
  /未成年/,
  /18歳未満/,
  /17歳/,
  /16歳/,
  /15歳/,
];

const STUDENT_ROLE_PATTERNS = [
  /生徒/,
  /学生/,
  /クラスメイト/,
  /学園/,
  /学校/,
  /制服/,
];

function flattenText(spec) {
  const chunks = [];
  const walk = (v) => {
    if (v == null) return;
    if (typeof v === "string" || typeof v === "number") chunks.push(String(v));
    else if (Array.isArray(v)) v.forEach(walk);
    else if (typeof v === "object") Object.values(v).forEach(walk);
  };
  walk(spec);
  return chunks.join("\n");
}

function fail(code, message) {
  return { ok: false, code, message };
}

function validateSpec(spec) {
  const errors = [];
  if (!spec || typeof spec !== "object") {
    return { ok: false, errors: [fail("SPEC_MISSING", "spec が無い")] };
  }

  if (spec.rating !== "adult_18") {
    errors.push(fail("RATING", "rating は adult_18 のみ。全年齢や曖昧なレーティングは拒否する"));
  }
  if (!spec.ai_disclosure || typeof spec.ai_disclosure !== "object") {
    errors.push(fail("AI_DISCLOSURE", "ai_disclosure が無い。販売時の虚偽申告事故を先に止める"));
  } else {
    const d = spec.ai_disclosure;
    if (!["ai_generated", "partial_ai", "ai_assist", "none"].includes(d.category)) {
      errors.push(fail("AI_CATEGORY", "ai_disclosure.category が不正"));
    }
    if (d.category !== "none" && (!d.where || String(d.where).trim().length < 8)) {
      errors.push(fail("AI_WHERE", "AI利用箇所を購入者に説明できる文が不足"));
    }
  }

  const characters = Array.isArray(spec.characters) ? spec.characters : [];
  if (characters.length < 1) {
    errors.push(fail("NO_CHAR", "登場人物がいない"));
  }
  for (const ch of characters) {
    if (typeof ch.age !== "number" || ch.age < 18) {
      errors.push(fail("AGE", `${ch.id || ch.name || "?"}: age は数値かつ 18 以上`));
    }
    if (ch.appearance_adult !== true) {
      errors.push(fail("APPEARANCE", `${ch.id || ch.name || "?"}: 見た目が成人であることの明示が無い`));
    }
    if (ch.real_person === true) {
      errors.push(fail("REAL_PERSON", `${ch.id || ch.name || "?"}: 実在人物は禁止`));
    }
    const roleText = `${ch.role || ""} ${ch.name || ""} ${ch.id || ""}`;
    if (STUDENT_ROLE_PATTERNS.some((re) => re.test(roleText))) {
      errors.push(fail("SCHOOL", `${ch.id || ch.name || "?"}: 学生・学園設定は本パイプラインでは拒否（誤認リスク）`));
    }
  }

  const text = flattenText(spec);
  for (const re of MINOR_PATTERNS) {
    if (re.test(text)) {
      errors.push(fail("MINOR_TERM", `未成年を想起させる語にヒット: ${re}`));
      break;
    }
  }

  const nodes = spec.nodes || [];
  const ids = new Set(nodes.map((n) => n.id));
  if (!spec.start || !ids.has(spec.start)) {
    errors.push(fail("START", "start が nodes に存在しない"));
  }
  for (const n of nodes) {
    if (!n.id || !n.type) errors.push(fail("NODE", "id/type 欠落の node"));
    if (n.type === "choice") {
      const opts = n.options || [];
      if (opts.length < 2) errors.push(fail("CHOICE", `${n.id}: 選択肢は2つ以上`));
      for (const o of opts) {
        if (o.goto && !ids.has(o.goto)) errors.push(fail("GOTO", `${n.id}: goto ${o.goto} が無い`));
      }
    }
    if (n.goto && !ids.has(n.goto) && n.type !== "end") {
      errors.push(fail("GOTO", `${n.id}: goto ${n.goto} が無い`));
    }
    if (n.type === "hscene" && n.participants) {
      for (const pid of n.participants) {
        const ch = characters.find((c) => c.id === pid);
        if (!ch) errors.push(fail("HSCENE_CHAR", `${n.id}: 参加者 ${pid} が characters に無い`));
      }
    }
  }

  return { ok: errors.length === 0, errors };
}

function assertSellable(spec) {
  const result = validateSpec(spec);
  if (!result.ok) {
    const msg = result.errors.map((e) => `${e.code}: ${e.message}`).join("\n");
    const err = new Error(msg);
    err.errors = result.errors;
    throw err;
  }
  return result;
}

module.exports = { validateSpec, assertSellable, flattenText };
