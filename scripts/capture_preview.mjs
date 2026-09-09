import { chromium } from "../frontend/node_modules/playwright/index.mjs";
import { fileURLToPath } from "node:url";
const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  const page = await browser.newPage({
    viewport: { width: 1000, height: 900 },
    reducedMotion: "reduce",
  });
  await page.goto(process.env.PREVIEW_URL || "http://127.0.0.1:8000");
  await page.getByRole("button", { name: "查看示例报告" }).click();
  await page.getByRole("article").waitFor();
  await page.addStyleTag({
    content: ".report-paper { width: 640px; padding: 28px 32px; }",
  });
  await page.evaluate(() => document.fonts.ready);
  await page.getByRole("article").scrollIntoViewIfNeeded();
  const box = await page.getByRole("article").boundingBox();
  await page.screenshot({
    path: fileURLToPath(
      new URL("../frontend/public/report-preview.png", import.meta.url),
    ),
    clip: { x: box.x, y: box.y, width: box.width, height: 420 },
  });
  console.log(
    await page.evaluate(() =>
      [...document.fonts].map((f) => ({ family: f.family, status: f.status })),
    ),
  );
} finally {
  await browser.close();
}
