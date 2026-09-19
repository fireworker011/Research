"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { validateSpec } = require("../src/compliance");
const seed = require("../data/seeds/sample-adult-adv.json");

describe("compliance", () => {
  it("accepts the adult seed", () => {
    const r = validateSpec(seed);
    assert.equal(r.ok, true, JSON.stringify(r.errors, null, 2));
  });

  it("rejects underage age field", () => {
    const bad = structuredClone(seed);
    bad.characters[0].age = 17;
    const r = validateSpec(bad);
    assert.equal(r.ok, false);
    assert.ok(r.errors.some((e) => e.code === "AGE"));
  });

  it("rejects school roles", () => {
    const bad = structuredClone(seed);
    bad.characters[0].role = "学園の生徒";
    const r = validateSpec(bad);
    assert.equal(r.ok, false);
    assert.ok(r.errors.some((e) => e.code === "SCHOOL"));
  });

  it("rejects loli keyword in text", () => {
    const bad = structuredClone(seed);
    bad.nodes[0].text = "ロリコン向け";
    const r = validateSpec(bad);
    assert.equal(r.ok, false);
    assert.ok(r.errors.some((e) => e.code === "MINOR_TERM"));
  });

  it("requires AI disclosure detail when generated", () => {
    const bad = structuredClone(seed);
    bad.ai_disclosure.where = "AI";
    const r = validateSpec(bad);
    assert.equal(r.ok, false);
    assert.ok(r.errors.some((e) => e.code === "AI_WHERE"));
  });
});
