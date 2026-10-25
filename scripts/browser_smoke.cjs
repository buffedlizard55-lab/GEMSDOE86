#!/usr/bin/env node
"use strict";
// Optional, one-time local UI regression. No competition request, score or slot.
// npm install --prefix .cache/browser playwright-core@1.64.1 @sparticuz/chromium@153.0.0
// NODE_PATH=.cache/browser/node_modules node scripts/browser_smoke.cjs http://127.0.0.1:8000/
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { chromium: playwright } = require("playwright-core");
const packageModule = require("@sparticuz/chromium");
const chromium = packageModule.default ?? packageModule;
const root = path.resolve(__dirname, "..");
const base = new URL(process.argv[2] || "http://127.0.0.1:8000/");
const artifactCount = JSON.parse(fs.readFileSync(path.join(root, "docs/evidence/download-inventory.json"), "utf8")).artifacts.length;
const projectCount = JSON.parse(fs.readFileSync(path.join(root, "docs/evidence/fleet-feed.json"), "utf8")).projects.length;
const pages = ["index.html", "executive-summary.html", "submit.html", "evidence.html", "hypotheses.html", "fleet.html", "sources.html", "irregularities.html", "research.html", "download-status.html", "h86-fvmb-forensics.html"];
const hash = bytes => crypto.createHash("sha256").update(bytes).digest("hex");

(async () => {
  const errors = [];
  // This Linux sandbox omits NSS/NSPR. Use the libraries bundled in the npm
  // Chromium package; do not fetch unpinned browser binaries or system packages.
  const bundle = path.join(path.dirname(require.resolve("@sparticuz/chromium")), "../bin/al2023.tar.br");
  const libraryDirectory = await packageModule.inflate(bundle);
  packageModule.setupLambdaEnvironment(path.join(libraryDirectory, "lib"));
  const browser = await playwright.launch({
    // Lambda's single-process/default graphics flags crash in this container.
    // Keep normal browser isolation (apart from the sandbox unavailable here).
    executablePath: await chromium.executablePath(),
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"], headless: true,
  });
  const report = {
    schema: "gems86.ui-smoke.v1", observed_utc: new Date().toISOString(),
    scope: "One-time local Chromium UI checks at the recorded page hashes, not organizer acceptance, external link verification, scientific clearance, or a continuously refreshed browser test.",
    origin: base.origin, browser_version: browser.version(), viewports: [],
    page_sha256: Object.fromEntries(pages.map(file => [file, hash(fs.readFileSync(path.join(root, "docs", file)))])),
    asset_sha256: Object.fromEntries(["site.css", "site.js"].map(file => [file, hash(fs.readFileSync(path.join(root, "docs/assets", file)))])),
  };
  try {
    for (const width of [1440, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 1000 }, acceptDownloads: true });
      const page = await context.newPage();
      page.on("pageerror", error => errors.push(error.message));
      page.on("response", response => {
        if (new URL(response.url()).origin === base.origin && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
      });
      for (const file of pages) {
        const response = await page.goto(new URL(file, base).href);
        assert.equal(response.status(), 200, file);
        assert.equal(await page.locator("h1").count(), 1, file);
        assert(await page.locator("footer").textContent().then(text => text.includes("No candidate authorized") || text.includes("DO NOT SUBMIT")), file);
        const layout = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth }));
        assert(layout.scroll <= layout.width, `Horizontal page overflow at ${width}px on ${file}: ${JSON.stringify(layout)}`);
      }
      await page.goto(new URL("index.html", base).href);
      const auditTiffLinks = page.locator("#downloads").getByRole("link", {
        name: "Download TIFF — audit only · DO NOT SUBMIT", exact: true });
      const auditZipLinks = page.locator("#downloads").getByRole("link", {
        name: "One-TIFF ZIP — audit only · DO NOT SUBMIT", exact: true });
      assert.equal(await auditTiffLinks.count(), artifactCount);
      assert.equal(await auditZipLinks.count(), artifactCount);
      await page.locator("article.artifact details").first().locator("summary").click();
      await page.getByRole("button", { name: "Copy hash", exact: true }).first().click();
      await page.waitForFunction(() => {
        const button = document.querySelector("button[data-copy-target]");
        return button.textContent === "Copied" || button.textContent === "Select text to copy";
      });
      const downloadPromise = page.waitForEvent("download");
      await auditTiffLinks.first().click();
      const download = await downloadPromise;
      const inventory = JSON.parse(fs.readFileSync(path.join(root, "docs/evidence/download-inventory.json"), "utf8"));
      const expected = inventory.artifacts[0];
      assert.equal(download.suggestedFilename(), path.basename(expected.file));
      assert.equal(hash(fs.readFileSync(await download.path())), expected.sha256, "Browser-downloaded TIFF SHA mismatch");
      await page.goto(new URL("fleet.html", base).href);
      assert.equal(await page.locator("#fleet-table tbody tr").count(), projectCount);
      await page.locator("#fleet-filter").fill("GEMSDOE32");
      assert.equal(await page.locator("#fleet-table tbody tr:visible").count(), 1);
      await page.locator("#fleet-filter").fill("no-such-project-unique-test");
      assert.equal(await page.locator("#fleet-table tbody tr:visible").count(), 0);
      await page.locator("#fleet-filter").fill("");
      assert.equal(await page.locator("#fleet-table tbody tr:visible").count(), projectCount);
      fs.mkdirSync(path.join(root, ".cache/ui"), { recursive: true });
      await page.goto(new URL("index.html", base).href);
      await page.screenshot({ path: path.join(root, `.cache/ui/dashboard-${width}.png`), fullPage: false });
      report.viewports.push({ width, height: 1000, pages_checked: pages.length, no_horizontal_overflow: true,
        downloads_each_format: artifactCount, browser_download_sha_matches: true, fleet_filter_passed: true });
      await context.close();
    }
    // Progressive enhancement: the essential decision and download links survive without JS.
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(new URL("index.html", base).href);
    assert.equal(await page.locator("#downloads").getByRole("link", {
      name: "Download TIFF — audit only · DO NOT SUBMIT", exact: true }).count(), artifactCount);
    assert((await page.locator("main").textContent()).includes("DO NOT SUBMIT"));
    report.without_javascript_decision_and_downloads_work = true;
    await context.close();
    assert.deepEqual(errors, [], "Browser errors or local HTTP failures");
    report.errors = errors;
    report.passed = true;
    const date = new Date().toISOString().slice(0, 10).replaceAll("-", "");
    const destination = path.join(root, `docs/evidence/ui-smoke-${date}.json`);
    fs.writeFileSync(destination, JSON.stringify(report, null, 2) + "\n");
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
