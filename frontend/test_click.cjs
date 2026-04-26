const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('BROWSER ERROR:', err.toString()));
  
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
  
  await new Promise(r => setTimeout(r, 1000));
  
  // enable debug mode
  const btns = await page.$$('button');
  for (const b of btns) {
    const text = await page.evaluate(el => el.textContent, b);
    if (text.includes('Debug Mode: OFF')) {
      await b.click();
      console.log('Clicked Debug Mode');
    }
  }
  
  await new Promise(r => setTimeout(r, 1000));
  
  // select a layout not sidebar
  await page.select('.layout-select', 'top');
  
  // click a tree
  const sidebars = await page.$$('.sidebar-list li');
  console.log("Found trees:", sidebars.length);
  if (sidebars.length > 0) {
    await sidebars[0].click();
    console.log("Clicked tree");
    await new Promise(r => setTimeout(r, 2000));
  }
  
  // click a node
  const nodes = await page.$$('.react-flow__node');
  if (nodes.length > 0) {
    await nodes[0].click();
    console.log("Clicked node");
    await new Promise(r => setTimeout(r, 1000));
  }
  
  // click mock grade A
  const mockBtns = await page.$$('button');
  for (const b of mockBtns) {
    const text = await page.evaluate(el => el.textContent, b);
    if (text === 'A+') {
      console.log('Clicking A+');
      await b.click();
      await new Promise(r => setTimeout(r, 1000));
      break;
    }
  }
  
  const html = await page.evaluate(() => document.body.innerHTML);
  if (html.includes('Excellent!')) {
    console.log("SUCCESS: Grade was rendered!");
  } else {
    console.log("FAIL: Grade was not rendered.");
  }
  
  await browser.close();
})();
