import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const sourceRoots = ["admin-dashboard/src", "user-app/src"];
const forbiddenPatterns = [
  { pattern: /<button\b/, message: "Use Button from @movu/ui instead of raw <button>." },
  { pattern: /<input\b/, message: "Use Input from @movu/ui instead of raw <input>." },
  { pattern: /<select\b/, message: "Use Select from @movu/ui instead of raw <select>." },
  {
    pattern: /className=["'][^"']*(primary-button|secondary-button|ghost-button|danger-button|icon-button|segmented-control|status-pill|status-badge|action-button|toast)[^"']*["']/,
    message: "Old base UI class found; use @movu/ui primitives."
  },
  {
    pattern: /export function (Button|Card|Input|Alert|Badge|Dialog|Tabs|Sheet|Switch|Select)\b/,
    message: "Base UI components must live in packages/ui/src/components."
  }
];

const violations = [];

for (const sourceRoot of sourceRoots) {
  await scanDirectory(path.join(root, sourceRoot));
}

if (violations.length) {
  console.error("UI usage check failed:\n");
  for (const violation of violations) {
    console.error(`${violation.file}:${violation.line}: ${violation.message}`);
    console.error(`  ${violation.text.trim()}`);
  }
  process.exit(1);
}

console.log("UI usage check passed.");

async function scanDirectory(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      await scanDirectory(fullPath);
      continue;
    }
    if (!/\.(tsx|ts|css)$/.test(entry.name)) continue;
    await scanFile(fullPath);
  }
}

async function scanFile(filePath) {
  const content = await readFile(filePath, "utf8");
  const lines = content.split("\n");
  lines.forEach((lineText, index) => {
    for (const rule of forbiddenPatterns) {
      if (rule.pattern.test(lineText)) {
        violations.push({
          file: path.relative(root, filePath),
          line: index + 1,
          message: rule.message,
          text: lineText
        });
      }
    }
  });
}
