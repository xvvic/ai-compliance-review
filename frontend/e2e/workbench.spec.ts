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
  await expect(page.getByLabel("RAG 检索增强")).toBeVisible();
  await page.getByRole("button", { name: "RAG 检索依据", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText(/预先生成的检索示例，未实时调用报告模型|示例引用数据，未实时调用 LightRAG 或模型/);
  await expect(page.locator("#evidence-S01")).toContainText(/第 \d+–\d+ 行/);
  await page.screenshot({ path: "../output/playwright/mobile-rag.png" });
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "[RAG:S01]", exact: true }).click();
  await expect(page.locator("#evidence-S01")).toHaveClass(/selected/);
  await page.keyboard.press("Escape");
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
  await expect(page.getByLabel("RAG 检索增强")).toContainText("已加入生成上下文");
  await page.getByRole("button", { name: "RAG 检索依据", exact: true }).click();
  await expect(page.locator("#evidence-S01")).toContainText("报告引用");
  await expect(page.locator("#evidence-S02")).not.toContainText("报告引用");
  await page.screenshot({ path: "../output/playwright/desktop-rag.png" });
  await page.keyboard.press("Escape");
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

test("no retrieval results produce no RAG indicators", async ({ page }) => {
  await newPage(page);
  await page.locator("input[type=file]").setInputFiles({ name: "empty.txt", mimeType: "text/plain", buffer: Buffer.from("NO_RAG") });
  await page.getByRole("button", { name: "开始审查", exact: true }).click();
  await expect(page.getByText("审查完成", { exact: true })).toBeVisible({ timeout: 20000 });
  await expect(page.getByLabel("RAG 检索增强")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "RAG 检索依据" })).toHaveCount(0);
  await page.reload();
  await expect(page.getByRole("article")).toBeVisible();
  await expect(page.getByLabel("RAG 检索增强")).toHaveCount(0);
});

test("legacy example without RAG remains compatible", async ({ page }) => {
  await page.route("**/api/example", async route => {
    const response = await route.fetch();
    const report = await response.json();
    delete report.rag;
    await route.fulfill({ json: report });
  });
  await newPage(page);
  await page.getByRole("button", { name: "查看示例报告" }).click();
  await expect(page.getByRole("article")).toBeVisible();
  await expect(page.getByLabel("RAG 检索增强")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "[RAG:S01]", exact: true })).toHaveCount(0);
});

test("Embedding settings test connection without echoing the saved key", async ({ page }) => {
  await newPage(page);
  await page.getByRole("button", { name: "设置", exact: true }).click();
  await page.getByRole("tab", { name: "知识库与 Embedding" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByLabel("Embedding API Key", { exact: true })).toHaveValue("");
  await expect(dialog.getByLabel("Embedding 模型", { exact: true })).toHaveAttribute("readonly", "");
  await expect(dialog).toContainText("38 份资料");
  await dialog.getByRole("button", { name: "测试 Embedding 连接" }).click();
  await expect(dialog).toContainText("Embedding 连接正常");
  await expect(dialog).not.toContainText("synthetic-rag-key");
  await page.screenshot({ path: "../output/playwright/desktop-embedding.png" });
});


test("embedding settings clear secrets and reject failed connections on mobile", async ({ page }) => {
  await newPage(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "设置", exact: true }).click();
  await page.getByRole("tab", { name: "知识库与 Embedding" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByText("高级：兼容 API 地址", { exact: true }).click();
  await dialog.getByLabel("Embedding API 地址", { exact: true }).fill("http://127.0.0.1:8011/embedding/wrong");
  await expect(dialog.getByText("清除已保存的 Embedding API Key")).toHaveCount(0);
  await dialog.getByLabel("Embedding API Key", { exact: true }).fill("synthetic-rag-key");
  await dialog.getByRole("button", { name: "测试 Embedding 连接" }).click();
  await expect(dialog.getByRole("alert")).toContainText("HTTP 404");
  await dialog.getByLabel("Embedding API 地址", { exact: true }).fill("http://127.0.0.1:8011/embedding/embeddings");
  await page.screenshot({ path: "../output/playwright/mobile-embedding.png" });
  await dialog.getByRole("checkbox", { name: "清除已保存的 Embedding API Key" }).check();
  await dialog.getByRole("button", { name: "保存设置" }).click();
  await expect(dialog).toBeHidden();
  await page.getByRole("button", { name: "设置", exact: true }).click();
  await page.getByRole("tab", { name: "知识库与 Embedding" }).click();
  await expect(page.getByRole("dialog").getByRole("checkbox", { name: "清除已保存的 Embedding API Key" })).toHaveCount(0);
  await page.getByRole("dialog").getByRole("button", { name: "测试 Embedding 连接" }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText("请填写 Embedding API Key");
});
