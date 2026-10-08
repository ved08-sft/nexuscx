const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'screenshot-from-test.png', fullPage: true });
  await browser.close();
  console.log('Screenshot taken successfully');
})();
