"use strict";

/**
 * 卸価格の公式表はサークル管理画面が正。ここは意思決定用の粗いモデル。
 * takeRate を「調べた事実」として書かないこと。
 */
const PLATFORM_CAPS = {
  dlsite_ai_generated: { worksPerMonth: 3, source: "DLsiteサークルヘルプ（AI生成作品の販売に関して）申請日基準・同一運営の複数サークル回避は不可" },
  fanza_ai_comic_cg_video: { worksPerMonth: 3, source: "FANZA同人公式ヘルプ（コミック/CG/動画の一部AI・AI生成）" },
  fanza_game_row: { worksPerMonth: 2, source: "FANZA公式表のゲーム行はセル結合で『毎月2作品』と読める。通常ゲーム全体かAIゲームのみかはHTML結合のため未確定。サークル登録後に原本確認" },
};

function requiredCopiesForProfit({ monthlyProfitYen, priceYen, takeRate }) {
  const unit = priceYen * takeRate;
  if (!(unit > 0)) return { ok: false, reason: "単価または取り分が 0" };
  return { ok: true, unitTakeYen: unit, copies: Math.ceil(monthlyProfitYen / unit) };
}

function projectMonth({
  priceYen,
  takeRate = 0.6,
  copiesPerWork,
  worksPerMonth,
  platformCap = 3,
  fixedCostYen = 0,
  monthlyProfitTargetYen = 2_000_000,
}) {
  const warnings = [];
  if (worksPerMonth > platformCap) {
    warnings.push(`worksPerMonth=${worksPerMonth} は cap=${platformCap} を超える。週1（≈4本/月）はフルAI前提だと販売枠で死ぬ`);
  }
  const unitTake = priceYen * takeRate;
  const gross = unitTake * copiesPerWork * worksPerMonth;
  const profit = gross - fixedCostYen;
  const need = requiredCopiesForProfit({
    monthlyProfitYen: monthlyProfitTargetYen,
    priceYen,
    takeRate,
  });
  const copiesNow = copiesPerWork * worksPerMonth;
  return {
    assumptions: {
      priceYen,
      takeRate,
      takeRateIsEstimate: true,
      copiesPerWork,
      worksPerMonth,
      platformCap,
      fixedCostYen,
    },
    unitTakeYen: unitTake,
    monthlyGrossTakeYen: gross,
    monthlyProfitYen: profit,
    copiesThisMonth: copiesNow,
    target: {
      monthlyProfitTargetYen,
      copiesNeededIfThisPrice: need.ok ? need.copies : null,
      gapCopies: need.ok ? need.copies - copiesNow : null,
    },
    warnings,
    kill: killCriteria({ copiesPerWork, worksPerMonth, profit, monthlyProfitTargetYen, platformCap }),
  };
}

function killCriteria({ copiesPerWork, worksPerMonth, profit, monthlyProfitTargetYen, platformCap }) {
  const rules = [];
  if (worksPerMonth === 0) {
    rules.push({ gate: "NO_SHIP", fail: true, text: "未出荷。仕組みの話を月利の話と混ぜない" });
  }
  if (worksPerMonth > platformCap) {
    rules.push({ gate: "CAP", fail: true, text: "販売上限を無視したペースは計画ではない" });
  }
  if (worksPerMonth >= 1 && copiesPerWork < 30) {
    rules.push({
      gate: "DEMAND_30",
      fail: copiesPerWork > 0 && copiesPerWork < 30,
      pending: copiesPerWork === 0,
      text: "初作30日で30本未満なら需要未証明。週次量産に進まない",
    });
  }
  if (profit < monthlyProfitTargetYen * 0.05 && worksPerMonth >= 1 && copiesPerWork > 0) {
    rules.push({
      gate: "SCALE_GAP",
      fail: true,
      text: "現状ペースでは目標の5%未満。本数を増やす前に単体の売れ方を直せ",
    });
  }
  return rules;
}

function defaultScenarios(priceYen = 2200) {
  return {
    note: "万灯あお氏のDLsiteゲーム中央値403本は『掲載作品の累計販売数の中央値』であり月次ではない。月次需要の証拠に使うな",
    scenarios: {
      zero: projectMonth({ priceYen, copiesPerWork: 0, worksPerMonth: 0, platformCap: 3 }),
      first_flop: projectMonth({ priceYen, copiesPerWork: 10, worksPerMonth: 1, platformCap: 3 }),
      first_ok: projectMonth({ priceYen, copiesPerWork: 80, worksPerMonth: 1, platformCap: 3 }),
      cap3_median_misread: projectMonth({ priceYen, copiesPerWork: 403, worksPerMonth: 3, platformCap: 3 }),
      target_200man_at_3works: projectMonth({
        priceYen,
        copiesPerWork: Math.ceil(
          requiredCopiesForProfit({ monthlyProfitYen: 2_000_000, priceYen, takeRate: 0.6 }).copies / 3
        ),
        worksPerMonth: 3,
        platformCap: 3,
      }),
      weekly_breaks_cap: projectMonth({ priceYen, copiesPerWork: 80, worksPerMonth: 4, platformCap: 3 }),
    },
  };
}

module.exports = { PLATFORM_CAPS, requiredCopiesForProfit, projectMonth, defaultScenarios };
