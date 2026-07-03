import { execFileSync } from "node:child_process";

const apiOrigin = process.env.MOVU_API_ORIGIN ?? "http://127.0.0.1:8000";

async function waitForHealth() {
  const deadline = Date.now() + 90_000;
  let lastError: unknown;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${apiOrigin}/health`);
      if (response.ok) return;
    } catch (err) {
      lastError = err;
    }
    await new Promise((resolve) => setTimeout(resolve, 1_000));
  }

  throw new Error(`Backend health check did not pass: ${String(lastError)}`);
}

export default async function globalSetup() {
  if (process.env.MOVU_E2E_SKIP_DOCKER !== "1") {
    execFileSync("docker", ["compose", "up", "-d", "backend"], { stdio: "inherit" });
  }

  await waitForHealth();

  if (process.env.MOVU_E2E_SKIP_SEED !== "1") {
    execFileSync("docker", ["compose", "exec", "-T", "backend", "python", "-m", "app.db.seed"], {
      stdio: "inherit"
    });
  }
}
