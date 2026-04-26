const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('BROWSER ERROR:', err.toString()));
  
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
  
  await new Promise(r => setTimeout(r, 2000));
  await browser.close();
})();
