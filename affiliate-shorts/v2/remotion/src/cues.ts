export type Cue = { start: number; end: number; lines: string[] };

export const cues: Record<string, Cue[]> = {
  "01": [
    { start: 0.0, end: 1.6, lines: ["千分の五。"] },
    { start: 1.6, end: 3.6, lines: ["令和八年四月から"] },
    { start: 3.6, end: 5.4, lines: ["来年の三月まで。"] },
    { start: 5.4, end: 7.6, lines: ["一般の事業なら"] },
    { start: 7.6, end: 9.6, lines: ["労働者の負担。"] },
    { start: 9.6, end: 12.0, lines: ["雇用保険は千分の五。"] },
    { start: 12.0, end: 14.6, lines: ["業種が違えば"] },
    { start: 14.6, end: 17.2, lines: ["率も変わる。"] },
    { start: 17.2, end: 20.0, lines: ["明細の行は雇用保険。"] },
    { start: 20.0, end: 22.0, lines: ["#PR", "出典は説明欄"] },
  ],
  "02": [
    { start: 0.0, end: 7.0, lines: ["その年金、", "全部あなたの負担？"] },
    { start: 7.0, end: 15.0, lines: ["料率は", "18.300パーセント。"] },
    { start: 15.0, end: 23.0, lines: ["平成二十九年九月から", "この率で固定。"] },
    { start: 23.0, end: 31.0, lines: ["会社と本人で", "半分ずつ。"] },
    { start: 31.0, end: 38.0, lines: ["本人の分は", "9.150パーセント。"] },
    { start: 38.0, end: 46.0, lines: ["賞与も同じ料率。", "厚生年金基金は別。"] },
    { start: 46.0, end: 48.0, lines: ["#PR", "料率は公式"] },
  ],
  "03": [
    { start: 0.0, end: 5.0, lines: ["明細の、通勤手当。"] },
    { start: 5.0, end: 11.0, lines: ["最も経済的で", "合理的な経路。"] },
    { start: 11.0, end: 17.0, lines: ["その定期代が", "非課税。"] },
    { start: 17.0, end: 24.0, lines: ["月十五万円が", "上限になる。"] },
    { start: 24.0, end: 32.0, lines: ["超えた分は給与。", "グリーン料金は別。"] },
    { start: 32.0, end: 34.0, lines: ["#PR", "上限の出典あり"] },
  ],
};
