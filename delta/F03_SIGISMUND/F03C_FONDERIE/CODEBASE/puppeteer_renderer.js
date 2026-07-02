#!/usr/bin/env node
/**
 * CRUSADER Delta — F03C LA FONDERIE
 * puppeteer_renderer.js
 *
 * Renders frames from a Canvas-based HTML file using Puppeteer.
 * Each frame is captured as a PNG screenshot.
 *
 * Usage:
 *   node puppeteer_renderer.js <html_file> <output_dir> [start_frame] [end_frame]
 *
 * Examples:
 *   node puppeteer_renderer.js test_minimal.html ./frames              # all frames
 *   node puppeteer_renderer.js test_minimal.html ./frames 0 29         # frames 0-29
 *   node puppeteer_renderer.js test_minimal.html ./frames 30 59        # frames 30-59
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function render() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('Usage: node puppeteer_renderer.js <html_file> <output_dir> [start_frame] [end_frame]');
    process.exit(1);
  }

  const htmlFile = path.resolve(args[0]);
  const outputDir = path.resolve(args[1]);
  const startFrame = args[2] !== undefined ? parseInt(args[2], 10) : null;
  const endFrame = args[3] !== undefined ? parseInt(args[3], 10) : null;

  // Create output directory
  fs.mkdirSync(outputDir, { recursive: true });

  console.log(`[FONDERIE] HTML: ${htmlFile}`);
  console.log(`[FONDERIE] Output: ${outputDir}`);

  // Launch browser
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--hide-scrollbars',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  // Load HTML
  // Use 'load' instead of 'networkidle0' — the animation loop keeps firing
  // network events, so networkidle0 never resolves on large inline HTML
  await page.goto(`file://${htmlFile}`, { waitUntil: 'load', timeout: 60000 });

  // Get config from the page
  const config = await page.evaluate(() => window.CRUSADER_CONFIG);
  console.log(`[FONDERIE] Config: ${JSON.stringify(config)}`);

  const totalFrames = config.TOTAL_FRAMES;
  const frameStart = startFrame !== null ? startFrame : 0;
  const frameEnd = endFrame !== null ? endFrame : totalFrames - 1;

  console.log(`[FONDERIE] Rendering frames ${frameStart} → ${frameEnd} (${frameEnd - frameStart + 1} frames)`);

  const t0 = Date.now();

  for (let i = frameStart; i <= frameEnd; i++) {
    // Call drawFrame on the page
    await page.evaluate((frameIndex) => {
      window.drawFrame(frameIndex);
    }, i);

    // Screenshot the canvas
    const canvasHandle = await page.$('#canvas');
    const paddedIndex = String(i).padStart(6, '0');
    const outPath = path.join(outputDir, `frame_${paddedIndex}.png`);

    await canvasHandle.screenshot({ path: outPath, type: 'png' });

    // Progress every 10 frames
    if ((i - frameStart) % 10 === 0 || i === frameEnd) {
      const elapsed = ((Date.now() - t0) / 1000).toFixed(1);
      const done = i - frameStart + 1;
      const total = frameEnd - frameStart + 1;
      const pct = ((done / total) * 100).toFixed(1);
      console.log(`[FONDERIE] Frame ${i}/${frameEnd} (${pct}%) — ${elapsed}s elapsed`);
    }
  }

  const totalTime = ((Date.now() - t0) / 1000).toFixed(1);
  const framesRendered = frameEnd - frameStart + 1;
  console.log(`[FONDERIE] ✅ Done! ${framesRendered} frames in ${totalTime}s (${(framesRendered / totalTime).toFixed(1)} fps)`);

  await browser.close();
}

render().catch((err) => {
  console.error('[FONDERIE] ❌ Fatal error:', err);
  process.exit(1);
});
