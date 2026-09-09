import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  fullyParallel: false,
  timeout: 45000,
  use: {
    baseURL: "http://127.0.0.1:8011",
    channel: "chrome",
    headless: true,
    reducedMotion: "reduce",
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure",
  },
  outputDir: "../output/playwright/test-results",
  reporter: [["list"]],
  webServer: {
    command: "..\\.venv\\Scripts\\python.exe ..\\tests\\serve_fixture.py",
    url: "http://127.0.0.1:8011/api/health",
    reuseExistingServer: false,
    timeout: 30000,
  },
});
