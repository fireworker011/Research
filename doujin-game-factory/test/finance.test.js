"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const { projectMonth, requiredCopiesForProfit } = require("../src/finance");

describe("finance", () => {
  it("computes copies for 2M at 2200 * 0.6", () => {
    const r = requiredCopiesForProfit({ monthlyProfitYen: 2_000_000, priceYen: 2200, takeRate: 0.6 });
    assert.equal(r.ok, true);
    assert.equal(r.unitTakeYen, 1320);
    assert.equal(r.copies, Math.ceil(2_000_000 / 1320));
  });

  it("flags weekly pace over DLsite AI cap", () => {
    const r = projectMonth({ priceYen: 2200, copiesPerWork: 80, worksPerMonth: 4, platformCap: 3 });
    assert.ok(r.warnings.some((w) => w.includes("週1")));
    assert.ok(r.kill.some((k) => k.gate === "CAP" && k.fail));
  });

  it("does not treat zero sales as a demand kill yet", () => {
    const r = projectMonth({ priceYen: 2200, copiesPerWork: 0, worksPerMonth: 0, platformCap: 3 });
    assert.ok(r.kill.some((k) => k.gate === "NO_SHIP"));
    assert.equal(r.monthlyProfitYen, 0);
  });
});
