const { chromium } = require('playwright');

(async () => {
  const url = process.argv[2];
  if (!url) {
    console.error("No URL provided");
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"});
  const page = await context.newPage();

  try {
    await page.goto(url, { waitUntil: 'load' });

    // Wait a little extra in case JS challenge
    await page.waitForTimeout(2000);

    const html = await page.content();
    console.log(html);
  } catch (err) {
    console.error("Navigation error:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();