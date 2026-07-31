import { gzipSync } from "node:zlib";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const DIST_ASSETS = join(process.cwd(), "dist", "assets");
const BUDGET_BYTES = 400 * 1024;

const jsFiles = readdirSync(DIST_ASSETS).filter((name) => name.endsWith(".js"));
const sizes = jsFiles.map((name) => {
  const bytes = readFileSync(join(DIST_ASSETS, name));
  const gzipped = gzipSync(bytes).length;
  return { name, gzipped };
});

const totalGzip = sizes.reduce((sum, entry) => sum + entry.gzipped, 0);

for (const entry of sizes) {
  console.log(`${entry.name}: ${(entry.gzipped / 1024).toFixed(2)} kB gzip`);
}

console.log(`Total JS gzip: ${(totalGzip / 1024).toFixed(2)} kB (budget ${BUDGET_BYTES / 1024} kB)`);

if (totalGzip > BUDGET_BYTES) {
  console.error("Bundle budget exceeded.");
  process.exit(1);
}
