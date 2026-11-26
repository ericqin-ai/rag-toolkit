/** Real Chrome/Edge screenshots via CDP. Node >=22; no npm dependencies. */
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const browser = process.env.RAG_BROWSER;
if (!browser) throw new Error('Set RAG_BROWSER to a Chrome or Edge executable.');
const appUrl = process.env.RAG_CAPTURE_URL || 'http://127.0.0.1:8507';
const parsedUrl = new URL(appUrl);
if (!['http:', 'https:'].includes(parsedUrl.protocol) || !['127.0.0.1','localhost','[::1]'].includes(parsedUrl.hostname) || parsedUrl.username || parsedUrl.password) throw new Error('Capture URL must be a credential-free loopback HTTP(S) URL.');
const output = path.join(root, 'docs/assets/screenshots');
const profile = await mkdtemp(path.join(tmpdir(), 'rag-capture-'));
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const chrome = spawn(browser, ['--headless=new', '--remote-debugging-port=0',
  `--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check',
  '--disable-background-networking', '--disable-component-update', '--window-size=1440,1000', 'about:blank'],
  { windowsHide: true, stdio: 'ignore' });
let ws;
try {
  let port;
  for (let i = 0; i < 100; i++) {
    try { port = (await readFile(path.join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]; break; }
    catch { await delay(100); }
  }
  if (!port) throw new Error('Browser did not open its local debugging endpoint.');
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(appUrl)}`,
    { method: 'PUT' })).json();
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  let sequence = 0;
  const pending = new Map();
  ws.onmessage = ({ data }) => {
    const message = JSON.parse(data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject, timer } = pending.get(message.id);
      clearTimeout(timer); pending.delete(message.id);
      message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result);
    }
  };
  const cdp = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 20000);
    pending.set(id, { resolve, reject, timer });
    ws.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async expression => {
    const result = await cdp('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const until = async (expression, label) => {
    for (let i = 0; i < 150; i++) {
      if (await evaluate(expression)) return;
      await delay(200);
    }
    console.error(await evaluate(`({titles:[...document.querySelectorAll('h2')].map(e=>e.textContent), radios:[...document.querySelectorAll('[data-testid="stSidebar"] input[type="radio"]')].map(e=>({value:e.value,checked:e.checked})), sidebar:document.querySelector('[data-testid="stSidebar"]')?.getBoundingClientRect().toJSON()})`));
    throw new Error(`UI timeout: ${label}`);
  };
  const clickText = async (selector, text) => {
    const point = await evaluate(`(() => { const e = [...document.querySelectorAll(${JSON.stringify(selector)})].find(e => e.textContent.trim() === ${JSON.stringify(text)}); if(!e) return null; e.scrollIntoView({block:'center'}); const r=e.getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2}; })()`);
    if (!point) throw new Error(`Control not found: ${text}`);
    await cdp('Input.dispatchMouseEvent', {type:'mousePressed',button:'left',clickCount:1,...point});
    await cdp('Input.dispatchMouseEvent', {type:'mouseReleased',button:'left',clickCount:1,...point});
  };
  const navigate = async view => {
    // On narrow screens, expose Streamlit's native collapsed sidebar.
    await evaluate(`(() => { const b = document.querySelector('button[aria-label="Expand sidebar"]'); if(b) b.click(); })()`);
    await until(`document.querySelector('[data-testid="stSidebar"]').getBoundingClientRect().left >= -1`, 'sidebar open');
    await delay(350);
    const changed = await evaluate(`(() => {const label=[...document.querySelectorAll('[data-testid="stSidebar"] label')].find(e=>e.textContent.trim()===${JSON.stringify(view)});if(!label)return false;label.click();return true;})()`);
    if (!changed) throw new Error(`Navigation unavailable: ${view}`);
    await until(`!![...document.querySelectorAll('h2')].find(e => e.textContent === ${JSON.stringify(view)})`, view);
    await until(`!document.querySelector('[data-testid="stSpinner"]')`, 'idle');
    await until(`document.querySelector('[data-testid="stApp"]').getAttribute('data-test-script-state') !== 'running'`, 'script completion');
    await delay(600);
  };
  await cdp('Page.enable');
  await cdp('Runtime.enable');
  await cdp('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  await until(`!!document.querySelector('[data-testid="stSidebar"]')`, 'sidebar');
  await until(`!!document.querySelector('[data-testid="stSidebar"] [role="combobox"]')`, 'language control');
  const combo = await evaluate(`(() => {const e=document.querySelector('[data-testid="stSidebar"] [role="combobox"]'); const r=e.getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
  await cdp('Input.dispatchMouseEvent', {type:'mousePressed',button:'left',clickCount:1,...combo});
  await cdp('Input.dispatchMouseEvent', {type:'mouseReleased',button:'left',clickCount:1,...combo});
  await until(`!![...document.querySelectorAll('[role="option"]')].find(e => e.textContent === 'English')`, 'language');
  await clickText('[role="option"]', 'English');
  await until(`document.body.innerText.includes('Navigation')`, 'English UI');
  await navigate('Datasets');
  await clickText('button', 'Load sample data');
  await until(`document.body.innerText.includes('Loaded 6 documents')`, 'sample data');
  await navigate('Search');
  await until(`!!document.querySelector('[data-testid="stTextInput"] input')`, 'query input');
  await evaluate(`document.querySelector('[data-testid="stTextInput"] input').focus()`);
  await cdp('Input.insertText', { text: 'FAISS CPU' });
  await clickText('button', 'Search');
  await until(`document.body.innerText.includes('Download results')`, 'search results');
  await navigate('Compare');
  await until(`!!document.querySelector('[data-testid="stTextInput"] input')`, 'comparison input');
  await evaluate(`document.querySelector('[data-testid="stTextInput"] input').focus()`);
  await cdp('Input.insertText', { text: 'FAISS CPU' });
  await clickText('button', 'Run comparison');
  await until(`document.body.innerText.includes('Download report')`, 'comparison');
  await navigate('Evaluation');
  await clickText('button', 'Run evaluation');
  await until(`document.body.innerText.includes('JSON')`, 'evaluation report');
  await mkdir(output, { recursive: true });
  const themeOnly = process.argv.includes('--theme-only');
  const captures = themeOnly ? JSON.parse(await readFile(path.join(output,'manifest.json'),'utf8')).captures.filter(c=>c.layout!=='desktop-dark') : [];
  for (const [layout, width, height] of (themeOnly ? [] : [['desktop', 1440, 1000], ['narrow', 390, 844]])) {
    await cdp('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
    for (const view of ['Overview', 'Search', 'Inspector', 'Compare', 'Evaluation', 'Datasets', 'Settings']) {
      await navigate(view);
      if (['Inspector', 'Evaluation'].includes(view)) {
        await until(`!!document.querySelector('[data-testid="stPlotlyChart"]')`, `${view} rendered chart`);
      }
      if (layout === 'narrow') {
        await evaluate(`(() => { const b = document.querySelector('button[aria-label="Collapse sidebar"]'); if(b) b.click(); })()`);
        await delay(300);
      }
      await evaluate(`document.querySelector('[data-testid="stMain"]').scrollTo(0, 0)`);
      const checks = await evaluate(`({title: document.querySelector('h2')?.textContent,
        exceptions: document.querySelectorAll('[data-testid="stException"]').length,
        viewportWidth: innerWidth, documentWidth: document.documentElement.scrollWidth})`);
      if (checks.exceptions || checks.documentWidth > width) throw new Error(`Layout/error check failed: ${view} ${layout}`);
      const file = `${view.toLowerCase()}-${layout}.png`;
      const screenshot = await cdp('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
      await writeFile(path.join(output, file), Buffer.from(screenshot.data, 'base64'));
      captures.push({ page: view, layout, width, height, file, ...checks });
      console.log(`${view} ${layout}: ${width}x${height}, exceptions=${checks.exceptions}, documentWidth=${checks.documentWidth}`);
      if (layout === 'desktop' && ['Inspector', 'Evaluation'].includes(view)) {
        await evaluate(`document.querySelector('[data-testid="stPlotlyChart"]').scrollIntoView({block:'center'})`);
        await delay(400);
        const chartFile = `${view.toLowerCase()}-chart-desktop.png`;
        const chart = await cdp('Page.captureScreenshot', {format:'png',captureBeyondViewport:false});
        await writeFile(path.join(output,chartFile),Buffer.from(chart.data,'base64'));
        captures.push({page:view,layout:'desktop-chart',width,height,file:chartFile,...checks});
      }
    }
  }
  await cdp('Emulation.setDeviceMetricsOverride', {width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await navigate('Search');
  const lightColor = await evaluate(`getComputedStyle(document.querySelector('h1')).color`);
  await cdp('Emulation.setEmulatedMedia', {features:[{name:'prefers-color-scheme',value:'dark'}]});
  await delay(800);
  const darkColor = await evaluate(`getComputedStyle(document.querySelector('h1')).color`);
  if (darkColor !== lightColor) {
    const dark = await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    await writeFile(path.join(output,'search-dark-desktop.png'),Buffer.from(dark.data,'base64'));
    captures.push({page:'Search',layout:'desktop-dark',width:1440,height:1000,
      file:'search-dark-desktop.png',lightColor,darkColor});
    console.log(`Native system theme: ${lightColor} -> ${darkColor}`);
  } else {
    await evaluate(`document.querySelector('[data-testid="stMainMenuButton"]').click()`);
    await until(`!!document.querySelector('[data-testid="stThemeSwitcher"]')`, 'native theme menu');
    const selected = await evaluate(`(() => { const item=[...document.querySelectorAll('[role="menuitemradio"]')].find(e=>e.textContent.includes('Dark')); return item?.textContent.trim();})()`);
    if (!selected) throw new Error('Native Dark theme option unavailable.');
    await evaluate(`(() => {const e=[...document.querySelectorAll('[role="menuitemradio"]')].find(e=>e.textContent.trim()===${JSON.stringify(selected)});e.click();})()`);
    await delay(800);
    await delay(800);
    await until(`getComputedStyle(document.querySelector('h1')).color !== ${JSON.stringify(lightColor)}`, 'native Dark theme');
    await cdp('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await cdp('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await delay(500);
    const dark = await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    await writeFile(path.join(output,'search-dark-desktop.png'),Buffer.from(dark.data,'base64'));
    captures.push({page:'Search',layout:'desktop-dark',width:1440,height:1000,
      file:'search-dark-desktop.png',theme:'Dark selected from the native Streamlit menu'});
    console.log('Native Dark theme selected and captured.');
  }
  await navigate('Inspector');
  await until(`!!document.querySelector('[data-testid="stPlotlyChart"]')`, 'Dark Plotly chart');
  await evaluate(`document.querySelector('[data-testid="stPlotlyChart"]').scrollIntoView({block:'center'})`);
  await delay(500);
  const darkChart = await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  await writeFile(path.join(output,'inspector-dark-desktop.png'),Buffer.from(darkChart.data,'base64'));
  captures.push({page:'Inspector',layout:'desktop-dark',width:1440,height:1000,
    file:'inspector-dark-desktop.png',theme:'Native Streamlit Dark with Plotly'});
  await writeFile(path.join(output, 'manifest.json'), JSON.stringify({
    captured_at: new Date().toISOString(), app_url: appUrl, data: 'Bundled MIT samples',
    purpose: 'Offline Pipeline Sanity Check', browser: await cdp('Browser.getVersion'), captures,
    note: 'Actual application viewport screenshots; not mockups. Long pages scroll below the frame.'
  }, null, 2) + '\n');
} finally {
  if (ws) ws.close();
  chrome.kill();
  // Only this script's mkdtemp-created browser profile is eligible for cleanup.
  if (profile.startsWith(path.join(tmpdir(), 'rag-capture-'))) {
    await delay(500);
    await rm(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 }).catch(() => {});
  }
}
