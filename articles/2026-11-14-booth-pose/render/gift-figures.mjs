import { chromium } from "playwright";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(root, "../line-kit/gift/figures");
const fontUrl = "../../fonts/NotoSansJP-VF.ttf";

const css = `
  @font-face {
    font-family: "Noto Sans JP";
    src: url("${fontUrl}") format("truetype");
    font-weight: 100 900;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #f3f0e7; }
  .sheet {
    width: 840px;
    background: #f3f0e7;
    color: #1a1814;
    padding: 32px 32px 36px;
    font-family: "Noto Sans JP", sans-serif;
    font-weight: 500;
  }
  h2 { font-size: 46px; line-height: 1.25; font-weight: 700; letter-spacing: 0.03em; }
  .lead { margin-top: 8px; font-size: 30px; line-height: 1.4; }
  .stack { display: flex; flex-direction: column; gap: 12px; margin-top: 18px; }
  .row { display: flex; gap: 12px; margin-top: 14px; }
  .card, .line {
    border: 3px solid #1a1814;
    background: #fbfaf6;
    padding: 14px 16px 16px;
  }
  .card { flex: 1; }
  .n { color: #8e2f1c; font-size: 28px; font-weight: 700; letter-spacing: 0.04em; }
  .t { font-size: 38px; font-weight: 700; line-height: 1.3; margin-top: 4px; }
  .d { font-size: 30px; line-height: 1.4; margin-top: 6px; }
  .bad { background: #f7ebe6; }
  .good { background: #eef3ee; }
  .line { display: grid; grid-template-columns: 86px 1fr; gap: 12px; align-items: center; }
  .tag { font-size: 28px; font-weight: 700; color: #8e2f1c; }
  .tx { font-size: 32px; font-weight: 700; line-height: 1.35; }
`;

function page(inner) {
  return `<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><style>${css}</style></head><body><div class="sheet">${inner}</div></body></html>`;
}

const sheets = {
  "fig-who": page(`
    <h2>誰の、どの止まり方か</h2>
    <p class="lead">商品の主語は、描く人の止まり方。僕の上手さではない。</p>
    <div class="stack">
      <div class="card"><p class="n">01</p><p class="t">誰が止まるか</p><p class="d">絵を描く人。資料を横に置きたい人。</p></div>
      <div class="card"><p class="n">02</p><p class="t">どこで止まるか</p><p class="d">動詞が決まらない。立つ、座る、伸びる。</p></div>
      <div class="card"><p class="n">03</p><p class="t">何を置くか</p><p class="d">練習・資料用の線画素体。線だけ。</p></div>
    </div>
  `),
  "fig-shelf": page(`
    <h2>棚の見方は、5手順</h2>
    <p class="lead">点数と価格の相場は、この図に書かない。見た事実だけ残す。</p>
    <div class="stack">
      <div class="line"><span class="tag">1</span><span class="tx">BOOTHをスマホで開く</span></div>
      <div class="line"><span class="tag">2</span><span class="tx">検索は1語。ポーズ集、など</span></div>
      <div class="line"><span class="tag">3</span><span class="tx">先頭の数件の題とサムネだけ見る</span></div>
      <div class="line"><span class="tag">4</span><span class="tx">繰り返す言葉を3つメモする</span></div>
      <div class="line"><span class="tag">5</span><span class="tx">薄かった動詞を1つ残す</span></div>
    </div>
  `),
  "fig-prompt": page(`
    <h2>プロンプトは、4部品</h2>
    <p class="lead">汎用の型。僕が打った文言ではない。</p>
    <div class="stack">
      <div class="card"><p class="n">1 何か</p><p class="t">線画素体。練習と資料</p></div>
      <div class="card"><p class="n">2 どう見えるか</p><p class="t">白い背景。黒い線。顔は簡素</p></div>
      <div class="card"><p class="n">3 入れないもの</p><p class="t">文字、衣装のデザイン、部屋</p></div>
      <div class="card"><p class="n">4 動詞は1つ</p><p class="t">全身が入る。余白がある</p></div>
    </div>
  `),
  "fig-inout": page(`
    <h2>入れる語と、外す語</h2>
    <div class="row">
      <div class="card good"><p class="n">入れる</p><p class="d">線画素体<br>練習と資料<br>白い背景<br>黒い線<br>顔は簡素<br>全身と余白<br>動詞は1つ</p></div>
      <div class="card bad"><p class="n">外す</p><p class="d">作家名と作品名<br>実在の人物名<br>文字<br>衣装のデザイン<br>表情の物語<br>角度の数字<br>動詞を2つ</p></div>
    </div>
  `),
  "fig-fix-a": page(`
    <h2>崩れと直し 前半</h2>
    <div class="stack">
      <div class="card"><p class="t">手・指</p><p class="d">読めなければ捨てる。本数は足さない。</p></div>
      <div class="card"><p class="t">足</p><p class="d">輪郭が線で読めるか。塊なら落とす。</p></div>
      <div class="card"><p class="t">接地</p><p class="d">足が床に着いているか。浮いたら落とす。</p></div>
      <div class="card"><p class="t">重心</p><p class="d">傾きが動詞と逆なら、動詞を1つに戻す。</p></div>
      <div class="card"><p class="t">左右</p><p class="d">左右を両方指定しない。保存後に向きを見る。</p></div>
    </div>
  `),
  "fig-fix-b": page(`
    <h2>崩れと直し 後半</h2>
    <div class="stack">
      <div class="card"><p class="t">線の太さ</p><p class="d">近いコマだけ紙面に戻す。</p></div>
      <div class="card"><p class="t">顔の情報</p><p class="d">表情の語は外す。顔は簡素な線。</p></div>
      <div class="card"><p class="t">文字が混ざる</p><p class="d">「文字は入れない」を毎回。出たら落とす。</p></div>
      <div class="card"><p class="t">背景が付く</p><p class="d">白い背景だけ。部屋が出たら落とす。</p></div>
      <div class="card"><p class="t">絵柄が寄る</p><p class="d">作家名、作品名、人物名は入れない。</p></div>
    </div>
  `),
  "fig-select": page(`
    <h2>拡大して見る4点</h2>
    <p class="lead">縮小の完成では、採用しない。</p>
    <div class="row">
      <div class="card"><p class="n">1</p><p class="t">手</p><p class="d">形が読める</p></div>
      <div class="card"><p class="n">2</p><p class="t">足</p><p class="d">形が読める</p></div>
    </div>
    <div class="row">
      <div class="card"><p class="n">3</p><p class="t">接地</p><p class="d">床に着く</p></div>
      <div class="card"><p class="n">4</p><p class="t">重心</p><p class="d">動詞と合う</p></div>
    </div>
  `),
  "fig-judge": page(`
    <h2>採用と、不採用</h2>
    <div class="row">
      <div class="card good"><p class="n">採用</p><p class="t">4点とも読める</p><p class="d">線の太さも、隣と近い。</p></div>
      <div class="card bad"><p class="n">不採用</p><p class="t">1点でも読めない</p><p class="d">雰囲気が良くても落とす。</p></div>
    </div>
    <p class="lead">同じ動詞ばかりの紙面も、ここで止める。</p>
  `),
  "fig-build": page(`
    <h2>スマホで組む順</h2>
    <div class="stack">
      <div class="line"><span class="tag">1</span><span class="tx">採用コマだけ残す</span></div>
      <div class="line"><span class="tag">2</span><span class="tx">正方形のキャンバスを作る</span></div>
      <div class="line"><span class="tag">3</span><span class="tx">4×4か4×2に置く</span></div>
      <div class="line"><span class="tag">4</span><span class="tx">余白を外側で揃える</span></div>
      <div class="line"><span class="tag">5</span><span class="tx">PNGで書き出す</span></div>
      <div class="line"><span class="tag">6</span><span class="tx">書き出し後にもう一度拡大</span></div>
    </div>
  `),
  "fig-sheet": page(`
    <h2>余白の置き方（計算の例）</h2>
    <p class="lead">数値は式の例。出力サイズが違えば、同じ式でやり直す。</p>
    <div class="card">
      <p class="t">外側40 ＋ コマ800 ＋ 間隔20</p>
      <p class="d">4コマなら、一辺は 40+800+20+800+20+800+20+800+40。</p>
      <p class="d">合計 3340。単位はpx。相場ではない。</p>
    </div>
    <div class="row">
      <div class="card"><p class="n">線</p><p class="t">PNG</p><p class="d">線が潰れにくい</p></div>
      <div class="card"><p class="n">複数枚</p><p class="t">ZIP</p><p class="d">中身はPNGのまま</p></div>
    </div>
  `),
  "fig-booth": page(`
    <h2>商品ページの順</h2>
    <div class="stack">
      <div class="line"><span class="tag">1</span><span class="tx">題名。動詞が分かる</span></div>
      <div class="line"><span class="tag">2</span><span class="tx">サムネ。中身の線が見える</span></div>
      <div class="line"><span class="tag">3</span><span class="tx">説明。誰の止まり方か</span></div>
      <div class="line"><span class="tag">4</span><span class="tx">ファイル。PNGかZIP</span></div>
      <div class="line"><span class="tag">5</span><span class="tx">タグ。検索した語を戻す</span></div>
      <div class="line"><span class="tag">6</span><span class="tx">年齢制限。線画でも画面で選ぶ</span></div>
    </div>
  `),
  "fig-thumb": page(`
    <h2>サムネで見せるもの</h2>
    <div class="row">
      <div class="card good"><p class="n">見せる</p><p class="t">線のコマ</p><p class="d">縮小でも動詞が1つ分かる</p></div>
      <div class="card bad"><p class="n">見せない</p><p class="t">小さい文字</p><p class="d">価格の主張。上手い絵の話</p></div>
    </div>
    <p class="lead">サムネは説明の代わりにしない。中身の線を見せる。</p>
  `),
  "fig-after": page(`
    <h2>出した日に見る数字</h2>
    <div class="stack">
      <div class="card"><p class="t">表示</p><p class="d">届いた数。売れた数ではない。</p></div>
      <div class="card"><p class="t">ブックマーク</p><p class="d">あとで使う判断。いいねの隣に置く。</p></div>
      <div class="card"><p class="t">リポストとリプ</p><p class="d">転送と会話は、別の箱。</p></div>
      <div class="card"><p class="t">販売</p><p class="d">棚の数字。ポストの数字と足さない。</p></div>
    </div>
  `),
  "fig-schedule": page(`
    <h2>12日の例。1日30分</h2>
    <p class="lead">例。僕の実測の日数ではない。</p>
    <div class="stack">
      <div class="line"><span class="tag">1</span><span class="tx">棚を見る</span></div>
      <div class="line"><span class="tag">2</span><span class="tx">動詞を1つ決める</span></div>
      <div class="line"><span class="tag">3</span><span class="tx">テンプレで出す</span></div>
      <div class="line"><span class="tag">4</span><span class="tx">動詞を変えて出す</span></div>
      <div class="line"><span class="tag">5</span><span class="tx">拡大して落とす</span></div>
      <div class="line"><span class="tag">6</span><span class="tx">短い文で出し直す</span></div>
      <div class="line"><span class="tag">7</span><span class="tx">枚数が足りるか見る</span></div>
      <div class="line"><span class="tag">8</span><span class="tx">紙面に組む</span></div>
      <div class="line"><span class="tag">9</span><span class="tx">説明文を書く</span></div>
      <div class="line"><span class="tag">10</span><span class="tx">サムネとファイル</span></div>
      <div class="line"><span class="tag">11</span><span class="tx">出品画面とガイドライン</span></div>
      <div class="line"><span class="tag">12</span><span class="tx">告知の下書きと記録</span></div>
    </div>
  `),
  "fig-stumble": page(`
    <h2>つまずきの見出し</h2>
    <p class="lead">本文に、直し方がある。</p>
    <div class="stack">
      <div class="line"><span class="tag">1</span><span class="tx">1枚に全部を任せる</span></div>
      <div class="line"><span class="tag">2</span><span class="tx">指示を足して崩す</span></div>
      <div class="line"><span class="tag">3</span><span class="tx">縮小のまま完成にする</span></div>
      <div class="line"><span class="tag">4</span><span class="tx">動詞が全部同じ</span></div>
      <div class="line"><span class="tag">5</span><span class="tx">左右を指定しすぎる</span></div>
      <div class="line"><span class="tag">6</span><span class="tx">線の太さを無視する</span></div>
      <div class="line"><span class="tag">7</span><span class="tx">文字や背景を残す</span></div>
      <div class="line"><span class="tag">8</span><span class="tx">作家名で絵柄を借りる</span></div>
      <div class="line"><span class="tag">9</span><span class="tx">練習と資料から外れる</span></div>
      <div class="line"><span class="tag">10</span><span class="tx">相場の数字を作る</span></div>
      <div class="line"><span class="tag">11</span><span class="tx">サムネに字を詰める</span></div>
      <div class="line"><span class="tag">12</span><span class="tx">12日を1日に詰める</span></div>
    </div>
  `),
};

const sheetDir = path.join(root, "html/gift-sheets");
await mkdir(sheetDir, { recursive: true });

const browser = await chromium.launch({
  executablePath: "/usr/bin/google-chrome",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars"],
});

await mkdir(outDir, { recursive: true });

try {
  const page = await browser.newPage({ viewport: { width: 900, height: 1400 }, deviceScaleFactor: 2 });
  for (const [name, html] of Object.entries(sheets)) {
    const htmlPath = path.join(sheetDir, `${name}.html`);
    await writeFile(htmlPath, html);
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.evaluate(async () => {
      await document.fonts.load("500 32px 'Noto Sans JP'");
      await document.fonts.load("700 46px 'Noto Sans JP'");
      await document.fonts.ready;
    });
    const box = await page.evaluate(() => {
      const sheet = document.querySelector(".sheet");
      const overflow = [...sheet.querySelectorAll("*")].some((el) => el.scrollWidth > el.clientWidth + 2);
      return { overflow, h: sheet.scrollHeight };
    });
    if (box.overflow) {
      throw new Error(`${name} overflows`);
    }
    const handle = await page.$(".sheet");
    const file = path.join(outDir, `${name}.png`);
    await handle.screenshot({ path: file });
    const buf = await readFile(file);
    console.log(`${name}.png ${buf.length} h=${box.h}`);
  }
} finally {
  await browser.close();
}
