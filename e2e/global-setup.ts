import { execFileSync } from "node:child_process";

const apiOrigin = process.env.MOVU_API_ORIGIN ?? "http://127.0.0.1:8000";

function commandOutput(command: string, args: string[]) {
  return execFileSync(command, args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
}

function commandExists(command: string) {
  try {
    execFileSync("which", [command], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function ensureDockerAvailable() {
  try {
    execFileSync("docker", ["info"], { stdio: "ignore" });
    return;
  } catch {
    // Continue below and try the local Colima runtime when available.
  }

  const dockerContext = (() => {
    try {
      return commandOutput("docker", ["context", "show"]);
    } catch {
      return "";
    }
  })();

  if (dockerContext === "colima" && commandExists("colima")) {
    console.log("Docker is unavailable and the active context is Colima. Starting Colima...");
    execFileSync("colima", ["start"], { stdio: "inherit" });
    execFileSync("docker", ["info"], { stdio: "ignore" });
    return;
  }

  throw new Error(
    [
      "Docker is not available, so MovU E2E cannot start the backend container.",
      "Start Docker Desktop, OrbStack, or Colima, then run `npm run e2e` again.",
      "If you already have a backend running, set MOVU_E2E_SKIP_DOCKER=1."
    ].join("\n")
  );
}

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
    ensureDockerAvailable();
    execFileSync("docker", ["compose", "up", "-d", "backend"], { stdio: "inherit" });
  }

  await waitForHealth();

  if (process.env.MOVU_E2E_SKIP_SEED !== "1") {
    execFileSync("docker", ["compose", "exec", "-T", "backend", "python", "-m", "app.db.seed"], {
      stdio: "inherit"
    });
  }
}
