const { chromium } = require('playwright');

(async () => {
  const data = JSON.parse(process.argv[2] || '{}');
  const url  = process.env.TARGET_URL;

  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto(url, { waitUntil: 'domcontentloaded' });

  if (data.first_name) await page.fill('#first_name', data.first_name);
  if (data.last_name)  await page.fill('#last_name',  data.last_name);
  if (data.email)      await page.fill('#email',      data.email);
  if (data.phone)      await page.fill('#phone',      data.phone);
  if (Array.isArray(data.skills)) {
    await page.fill('#skills', data.skills.join(', '));
  }

  await page.click('button[type="submit"]');
  await page.waitForLoadState('networkidle');
  console.log('OK');
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
