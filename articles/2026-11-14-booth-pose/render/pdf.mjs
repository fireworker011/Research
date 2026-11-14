import { chromium } from "playwright";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const giftDir = path.resolve(root, "../line-kit/gift");
const sources = ["checklist.md", "description-template.md", "work-log.md"];
const outPath = path.join(giftDir, "pose-kit.pdf");

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function markdownToHtml(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const parts = [];
  let inList = false;
  const closeList = () => {
    if (inList) {
      parts.push("</ul>");
      inList = false;
    }
  };
  for (const line of lines) {
    if (line.startsWith("# ")) {
      closeList();
      parts.push(`<h1>${escapeHtml(line.slice(2))}</h1>`);
    } else if (line.startsWith("## ")) {
      closeList();
      parts.push(`<h2>${escapeHtml(line.slice(3))}</h2>`);
    } else if (line.startsWith("- ")) {
      if (!inList) {
        parts.push("<ul>");
        inList = true;
      }
      parts.push(`<li>${escapeHtml(line.slice(2))}</li>`);
    } else if (line.trim() === "") {
      closeList();
    } else {
      closeList();
      parts.push(`<p>${escapeHtml(line)}</p>`);
    }
  }
  closeList();
  return parts.join("\n").replace(/【要確認:[^】]*】/g, '<span class="blank">$&</span>');
}

const chapters = [];
for (const name of sources) {
  const markdown = await readFile(path.join(giftDir, name), "utf8");
  chapters.push(`<article class="chapter">${markdownToHtml(markdown)}</article>`);
}

const fontUrl = pathToFileURL(path.join(root, "fonts/NotoSansJP-VF.ttf")).href;
const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8" />
<style>
  @font-face {
    font-family: "Noto Sans JP";
    src: url("${fontUrl}") format("truetype");
    font-weight: 100 900;
    font-style: normal;
  }
  @page { size: 108mm 190mm; margin: 10mm 8mm 12mm; }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    color: #1a1814;
    font-family: "Noto Sans JP", sans-serif;
    font-weight: 500;
    font-size: 14.5pt;
    line-height: 1.6;
  }
  h1 { font-size: 20pt; font-weight: 700; line-height: 1.35; margin: 0 0 0.6em; }
  h2 { font-size: 16pt; font-weight: 700; line-height: 1.4; margin: 1em 0 0.35em; }
  p { margin: 0.4em 0; }
  ul { margin: 0.2em 0 0.6em; padding-left: 1.2em; }
  li { margin: 0.28em 0; }
  .blank { font-weight: 700; }
  .chapter + .chapter { break-before: page; }
</style>
</head>
<body>
${chapters.join("\n")}
</body>
</html>`;

const htmlPath = path.join(root, "html/gift-print.html");
await writeFile(htmlPath, html);

const browser = await chromium.launch({
  executablePath: "/usr/bin/google-chrome",
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
try {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
  await page.evaluate(async () => {
    await document.fonts.load("500 16pt 'Noto Sans JP'");
    await document.fonts.load("700 20pt 'Noto Sans JP'");
    await document.fonts.ready;
  });
  await mkdir(giftDir, { recursive: true });
  await page.pdf({
    path: outPath,
    printBackground: true,
    preferCSSPageSize: true,
  });
} finally {
  await browser.close();
}

console.log(outPath);
