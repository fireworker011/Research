import { chromium } from "playwright";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const articleRoot = path.resolve(root, "..");

const pages = [
  { file: "thumbnail.html", out: "images/thumbnail.png", width: 1500, height: 600 },
  { file: "fig1.html", out: "images/fig1.png", width: 1600, height: 900 },
  { file: "fig2.html", out: "images/fig2.png", width: 1600, height: 900 },
  { file: "fig3.html", out: "images/fig3.png", width: 1600, height: 900 },
  { file: "fig4.html", out: "images/fig4.png", width: 1600, height: 900 },
  { file: "line-cta.html", out: "images/line-cta.png", width: 1600, height: 600 },
  {
    file: "richmenu.html",
    out: "line-kit/richmenu/richmenu.png",
    width: 2500,
    height: 1686,
    maxBytes: 1024 * 1024,
  },
];

function pngSize(buffer) {
  return {
    width: buffer.readUInt32BE(16),
    height: buffer.readUInt32BE(20),
  };
}

const browser = await chromium.launch({
  executablePath: "/usr/bin/google-chrome",
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars", "--font-render-hinting=none"],
});

try {
  for (const pageSpec of pages) {
    const page = await browser.newPage({
      viewport: { width: pageSpec.width, height: pageSpec.height },
      deviceScaleFactor: 1,
    });
    const htmlPath = path.join(root, "html", pageSpec.file);
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
    await page.evaluate(async () => {
      await document.fonts.load("500 64px 'Noto Sans JP'");
      await document.fonts.load("700 64px 'Noto Sans JP'");
      await document.fonts.ready;
      const probe = document.querySelector("h1") || document.querySelector(".t");
      const family = getComputedStyle(probe).fontFamily;
      if (!family.includes("Noto Sans JP")) {
        throw new Error(`Noto Sans JP did not apply (${family})`);
      }
    });

    const fit = await page.evaluate(() => {
      const frame = document.querySelector(".frame") || document.querySelector(".page");
      return {
        frameOverflow: frame.scrollHeight > frame.clientHeight + 1 || frame.scrollWidth > frame.clientWidth + 1,
        frameScrollHeight: frame.scrollHeight,
        frameClientHeight: frame.clientHeight,
        text: document.body.innerText.replace(/\s+/g, " ").trim(),
      };
    });
    if (fit.frameOverflow) {
      throw new Error(`${pageSpec.file} overflows the frame (${fit.frameScrollHeight} > ${fit.frameClientHeight})`);
    }

    const outPath = path.join(articleRoot, pageSpec.out);
    await mkdir(path.dirname(outPath), { recursive: true });
    await page.screenshot({ path: outPath, type: "png" });
    await page.close();

    const buffer = await readFile(outPath);
    const size = pngSize(buffer);
    if (size.width !== pageSpec.width || size.height !== pageSpec.height) {
      throw new Error(`${pageSpec.out} is ${size.width}x${size.height}`);
    }
    if (pageSpec.maxBytes && buffer.length > pageSpec.maxBytes) {
      throw new Error(`${pageSpec.out} is ${buffer.length} bytes`);
    }
    console.log(`${pageSpec.out} ${size.width}x${size.height} ${buffer.length} ${fit.text}`);
  }
} finally {
  await browser.close();
}
