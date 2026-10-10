"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { emitEventCode } = require("../src/emit-event-code");
const seed = require("../data/seeds/sample-adult-adv.json");

describe("event-code", () => {
  it("emits pasteable Wolf event code for the adult seed", () => {
    const txt = emitEventCode(seed);
    assert.match(txt, /^WoditorEvCOMMAND_START\n/);
    assert.match(txt, /\nWoditorEvCOMMAND_END\n$/);
    assert.match(txt, /\[101\]\[0,1\]<0>\(\)\("【森 健太】/);
    assert.match(txt, /\[102\]\[1,2\]<0>\(50\)\("タクシーで帰る","残る（成人向けルート）"\)/);
    assert.match(txt, /\[401\]\[1,0\]<0>\(2\)\(\)/);
    assert.match(txt, /\[401\]\[1,0\]<0>\(3\)\(\)/);
    assert.match(txt, /\[499\]\[0,0\]<0>\(\)\(\)/);
    assert.match(txt, /【Hシーン】/);
  });

  it("refuses underage spec", () => {
    const bad = structuredClone(seed);
    bad.characters[0].age = 12;
    assert.throws(() => emitEventCode(bad));
  });
});
