import { test, expect } from "@playwright/test";

async function newPage(page: any) {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "设置", exact: true }),
  ).toBeEnabled();
  const current = await page.request.get("/api/review/current");
  const job = await current.json();
  if (job?.status === "running") {
    const token = (await (await page.request.get("/api/session")).json()).token;
    await page.request.post(`/api/review/${job.id}/cancel`, {
      headers: { "x-session-token": token },
    });
    await page.reload();
    await expect(page.getByRole("button", { name: "新建审查" })).toBeEnabled();
  }
  await page.getByRole("button", { name: "新建审查" }).click();
  const confirm = page.getByRole("dialog");
  if (await confirm.isVisible())
    await confirm.getByRole("button", { name: "新建审查" }).click();
  await expect(page.getByRole("heading", { name: "待审查材料" })).toBeVisible();
}

test("desktop and mobile layouts, offline example and report inspection", async ({
  page,
}) => {
  await newPage(page);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: "../output/playwright/desktop-1440.png" });
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.screenshot({ path: "../output/playwright/desktop-1920.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../output/playwright/mobile-390.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  const bounds = await page.locator(".intake-footer").boundingBox();
  const footer = await page.locator(".page-footer").boundingBox();
  expect(bounds!.y + bounds!.height).toBeLessThan(footer!.y);
  await page.route("**/*", (route) =>
    route.request().url().startsWith("http://127.0.0.1:8011")
      ? route.continue()
      : route.abort(),
  );
  await page.getByRole("button", { name: "查看示例报告" }).click();
  await expect(page.getByRole("article")).toBeVisible();
  await page.screenshot({ path: "../output/playwright/mobile-report.png" });
  await page.getByRole("tab", { name: /风险清单/ }).click();
  await expect(page.getByRole("table")).toBeVisible();
  await page
    .getByRole("button", { name: "查看 DATA-003", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByText("风险依据")).toBeVisible();
  await page.screenshot({
    path: "../output/playwright/mobile-risk-drawer.png",
  });
  await page.keyboard.press("Escape");
  await page.getByRole("tab", { name: "人工复核" }).click();
  await expect(page.getByRole("button", { name: "提交复核" })).toBeDisabled();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole("tab", { name: "审查报告" }).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: "../output/playwright/desktop-report.png" });
});

test("upload, stream, refresh recovery, export and human review", async ({
  page,
}) => {
  await newPage(page);
  await page.locator("input[type=file]").setInputFiles({
    name: "企业材料.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("企业将个人信息跨境传输至境外。涉及未成年人信息。"),
  });
  await expect(page.getByText("企业材料.txt", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "开始审查", exact: true }).click();
  await expect(page.getByRole("heading", { name: "审查进行中" })).toBeVisible();
  await page.reload();
  await expect(page.getByText("审查完成", { exact: true })).toBeVisible({
    timeout: 20000,
  });
  await expect(page.getByRole("article")).toContainText("自动化测试报告");
  await page.getByRole("button", { name: "下载报告" }).click();
  const downloaded = page.waitForEvent("download");
  await page.getByText("Markdown 报告", { exact: true }).click();
  expect((await downloaded).suggestedFilename()).toBe("compliance_report.md");
  await page.getByRole("tab", { name: "人工复核" }).click();
  const selects = page
    .locator(".decision-controls .ant-select")
    .filter({ has: page.locator('input[aria-label$="复核动作"]') });
  for (let i = 0; i < (await selects.count()); i++) {
    await selects.nth(i).locator("input").press("ArrowDown");
    await selects.nth(i).locator("input").press("Enter");
  }
  await page.getByRole("button", { name: "提交复核" }).click();
  await expect(page.getByText("复核已保存", { exact: true })).toBeVisible();
  await page.reload();
  await page.getByRole("tab", { name: "人工复核" }).click();
  await expect(page.getByRole("button", { name: "提交复核" })).toBeDisabled();
});

test("model failure remains failed and a running review can be cancelled", async ({
  page,
}) => {
  await newPage(page);
  await page.locator("input[type=file]").setInputFiles({
    name: "失败测试.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("FAIL 企业材料"),
  });
  await page.getByRole("button", { name: "开始审查", exact: true }).click();
  await expect(page.getByRole("heading", { name: "审查失败" })).toBeVisible({
    timeout: 20000,
  });
  await expect(page.getByText("审查完成", { exact: true })).toHaveCount(0);
  await newPage(page);
  await page.locator("input[type=file]").setInputFiles({
    name: "取消测试.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("SLOW 企业材料"),
  });
  await page.getByRole("button", { name: "开始审查", exact: true }).click();
  await page.getByRole("button", { name: "取消审查" }).click();
  await expect(page.getByRole("heading", { name: "已取消" })).toBeVisible();
});

test("settings and invalid document show actionable states without secret echo", async ({
  page,
}) => {
  await newPage(page);
  await page.locator("input[type=file]").setInputFiles({
    name: "损坏.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("broken"),
  });
  await expect(page.getByRole("alert")).toContainText("文件解析失败");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "设置", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByLabel("模型密钥", { exact: true })).toHaveValue("");
  await page.screenshot({ path: "../output/playwright/mobile-settings.png" });
  await expect(dialog.getByRole("button", { name: "保存设置" })).toBeVisible();
});
