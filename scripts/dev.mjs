import { execFileSync, spawnSync } from "node:child_process";

const apiOrigin = process.env.MOVU_API_ORIGIN ?? "http://127.0.0.1:8000";

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    stdio: options.stdio ?? "inherit",
    encoding: "utf8",
    ...options
  });

  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed with exit code ${result.status ?? "unknown"}`);
  }

  return result.stdout?.trim() ?? "";
}

function output(command, args) {
  return execFileSync(command, args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"]
  }).trim();
}

function commandExists(command) {
  try {
    execFileSync("which", [command], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function ensureDockerAvailable() {
  if (!commandExists("docker")) {
    throw new Error("Docker is not installed. Install Docker Desktop, OrbStack, or Colima first.");
  }

  try {
    run("docker", ["info"], { stdio: "ignore" });
    return;
  } catch {
    // Try to recover common local Mac setup below.
  }

  let dockerContext = "";
  try {
    dockerContext = output("docker", ["context", "show"]);
  } catch {
    // Keep the generic error below.
  }

  if (dockerContext === "colima" && commandExists("colima")) {
    console.log("Docker is unavailable and the active context is Colima. Starting Colima...");
    run("colima", ["start"]);
    run("docker", ["info"], { stdio: "ignore" });
    return;
  }

  throw new Error(
    [
      "Docker is not running.",
      "Start Docker Desktop, OrbStack, or Colima, then run `npm run dev` again.",
      dockerContext ? `Current Docker context: ${dockerContext}` : "No Docker context could be detected."
    ].join("\n")
  );
}

async function waitForBackend() {
  const deadline = Date.now() + 120_000;
  let lastError;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${apiOrigin}/health`);
      if (response.ok) return;
    } catch (error) {
      lastError = error;
    }

    await new Promise((resolve) => setTimeout(resolve, 1_000));
  }

  throw new Error(`Backend did not become healthy at ${apiOrigin}/health: ${String(lastError)}`);
}

async function main() {
  console.log("Starting MovU...");
  ensureDockerAvailable();

  run("docker", ["compose", "up", "--build", "-d"]);
  await waitForBackend();

  console.log("Seeding local development data...");
  run("docker", ["compose", "exec", "-T", "backend", "python", "-m", "app.db.seed"]);

  run("docker", ["compose", "ps"]);

  console.log("");
  console.log("MovU is running:");
  console.log("- User app:        http://localhost:5174");
  console.log("- Admin dashboard: http://localhost:5173");
  console.log("- Backend API:     http://localhost:8000");
  console.log("");
  console.log("Sample login:");
  console.log("- Admin: admin@taylors.edu.my / Password123");
  console.log("- Rider: aina@sd.taylors.edu.my / Password123");
  console.log("- Driver: daniel@sd.taylors.edu.my / Password123");
  console.log("");
  console.log("Useful commands:");
  console.log("- npm run logs");
  console.log("- npm run stop");
}

main().catch((error) => {
  console.error("");
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
