import { defineConfig, devices } from "@playwright/test";

const userAppUrl = process.env.MOVU_USER_APP_URL ?? "http://127.0.0.1:6174";
const adminAppUrl = process.env.MOVU_ADMIN_APP_URL ?? "http://127.0.0.1:6173";
const apiUrl = process.env.MOVU_API_URL ?? "http://127.0.0.1:8000/api";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: {
    timeout: 10_000
  },
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: userAppUrl,
    trace: "retain-on-failure"
  },
  globalSetup: "./e2e/global-setup.ts",
  webServer: [
    {
      command: `cd user-app && VITE_API_BASE_URL=${apiUrl} npm run dev -- --host 127.0.0.1 --port 6174`,
      url: userAppUrl,
      reuseExistingServer: true,
      timeout: 90_000
    },
    {
      command: `cd admin-dashboard && VITE_API_BASE_URL=${apiUrl} npm run dev -- --host 127.0.0.1 --port 6173`,
      url: adminAppUrl,
      reuseExistingServer: true,
      timeout: 90_000
    }
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});
