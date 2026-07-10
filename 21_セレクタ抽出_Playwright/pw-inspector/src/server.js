const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

app.use(express.static(path.join(__dirname, '../public')));
app.use(express.json());

let browser = null;
let page = null;
let clients = new Set();

// ============================================================
// セッション管理
// ============================================================
let currentSession = null;

function getOrCreateSession(url) {
  if (!currentSession || currentSession.url !== url) {
    currentSession = {
      url,
      name: urlToName(url),
      createdAt: new Date().toISOString(),
      elements: {},
    };
  }
  return currentSession;
}

function urlToName(url) {
  try {
    const u = new URL(url);
    const parts = u.pathname.replace(/^\/|\/$/g, '').split('/').filter(Boolean);
    return parts.length ? parts[parts.length - 1] : u.hostname.replace(/\./g, '-');
  } catch (e) { return 'page'; }
}

function autoKey(info) {
  const raw = info.labelText || info.placeholder || info.ariaLabel
    || info.innerText || info.id || info.name || info.tagName;
  return toCamelCase(raw.slice(0, 40));
}

function toCamelCase(str) {
  const words = str.replace(/[^\w\s]/g, ' ').trim().split(/\s+/).filter(Boolean);
  if (!words.length) return 'element';
  return words.map((w, i) =>
    i === 0 ? w[0].toLowerCase() + w.slice(1) : w[0].toUpperCase() + w.slice(1)
  ).join('');
}

// ============================================================
// エクスポート生成
// ============================================================
function buildExportJSON(session) {
  const elements = {};
  for (const [key, el] of Object.entries(session.elements)) {
    elements[key] = {
      _memo: el.memo || '',
      _tag: el.tag,
      best: el.best,
      candidates: el.candidates,
      attrs: el.attrs,
      capturedAt: el.capturedAt,
    };
  }
  return {
    url: session.url,
    name: session.name,
    createdAt: session.createdAt,
    exportedAt: new Date().toISOString(),
    elements,
  };
}

function buildExportJS(session) {
  const varName = toCamelCase(session.name) + 'Selectors';
  const helperCode = `/**
 * ${session.name} - Playwright Selectors
 * URL: ${session.url}
 * Generated: ${new Date().toISOString()}
 */

/**
 * @param {import('@playwright/test').Page} page
 * @param {object} sel  selectors[key].best
 * @returns {import('@playwright/test').Locator}
 */
function resolveLocator(page, sel) {
  const { type, selector, code } = sel;
  switch (type) {
    case 'role': {
      const m = code.match(/getByRole\\\\('([^']+)',\\\\s*\\\\{[^}]*name:\\\\s*'([^']+)'/);
      if (m) return page.getByRole(m[1], { name: m[2] });
      break;
    }
    case 'label': {
      const m = code.match(/getByLabel\\\\('([^']+)'\\\\)/);
      if (m) return page.getByLabel(m[1]);
      break;
    }
    case 'placeholder': {
      const m = code.match(/getByPlaceholder\\\\('([^']+)'\\\\)/);
      if (m) return page.getByPlaceholder(m[1]);
      break;
    }
    case 'text': {
      const m = code.match(/getByText\\\\('([^']+)'/);
      if (m) return page.getByText(m[1], { exact: true });
      break;
    }
    case 'testid': {
      const m = code.match(/getByTestId\\\\('([^']+)'\\\\)/);
      if (m) return page.getByTestId(m[1]);
      break;
    }
    default:
      return page.locator(selector);
  }
  return page.locator(selector);
}

`;

  const lines = [];
  for (const [key, el] of Object.entries(session.elements)) {
    if (el.memo) lines.push(`  /** ${el.memo} */`);
    const bestStr = JSON.stringify(el.best, null, 4).replace(/\n/g, '\n  ');
    lines.push(`  ${key}: ${bestStr},\n`);
  }

  return helperCode
    + `const ${varName} = {\n${lines.join('\n')}};\n\n`
    + `function getLocator(page, key) {\n`
    + `  const sel = ${varName}[key];\n`
    + `  if (!sel) throw new Error('Selector key "' + key + '" not found');\n`
    + `  return resolveLocator(page, sel);\n`
    + `}\n\n`
    + `module.exports = { ${varName}, getLocator };\n`;
}

// ============================================================
// 要素解析
// ============================================================
async function analyzeElement(elementHandle, pageInstance) {
  return await pageInstance.evaluate((el) => {
    const attrs = {};
    for (const attr of el.attributes) attrs[attr.name] = attr.value;

    const innerText = el.innerText?.trim().slice(0, 80) || '';
    const rect = el.getBoundingClientRect();
    const role = el.getAttribute('role') ||
      (el.tagName.toLowerCase() === 'input' && attrs.type === 'button' ? 'button' : el.tagName.toLowerCase());
    const ariaLabel = el.getAttribute('aria-label') || '';

    let labelText = '';
    if (el.id) {
      const lbl = document.querySelector('label[for="' + el.id + '"]');
      if (lbl) labelText = lbl.innerText?.trim() || '';
    }
    if (!labelText) {
      const cl = el.closest('label');
      if (cl) labelText = cl.innerText?.trim() || '';
    }

    const placeholder = el.getAttribute('placeholder') || '';
    const testAttrs = {};
    ['data-testid', 'data-cy', 'data-qa', 'data-test', 'data-id', 'data-automation'].forEach(a => {
      if (attrs[a]) testAttrs[a] = attrs[a];
    });

    const classes = Array.from(el.classList).filter(c =>
      !c.match(/^(js-|is-|has-|active|disabled|hidden|visible|\w{1,2}$|col-|row-)/) && c.length > 2
    );

    function getXPath(element) {
      if (element.id) return '//*[@id="' + element.id + '"]';
      const parts = [];
      let cur = element;
      while (cur && cur.nodeType === Node.ELEMENT_NODE) {
        let idx = 1;
        let sib = cur.previousElementSibling;
        while (sib) { if (sib.tagName === cur.tagName) idx++; sib = sib.previousElementSibling; }
        const tag = cur.tagName.toLowerCase();
        parts.unshift(idx > 1 || cur.nextElementSibling?.tagName === cur.tagName ? tag + '[' + idx + ']' : tag);
        cur = cur.parentElement;
      }
      return '/' + parts.join('/');
    }

    return {
      tagName: el.tagName.toLowerCase(),
      id: el.id || '', role, ariaLabel, labelText, placeholder,
      innerText, value: el.value || '', testAttrs, classes,
      name: attrs.name || '', type: attrs.type || '', href: attrs.href || '',
      xpath: getXPath(el), allAttrs: attrs,
      rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
    };
  }, elementHandle);
}

function esc(str) { return String(str || '').replace(/'/g, "\\'"); }

function normalizeRole(role) {
  const map = { a: 'link', button: 'button', input: 'textbox', select: 'combobox',
    textarea: 'textbox', img: 'img', h1: 'heading', h2: 'heading', h3: 'heading',
    ul: 'list', li: 'listitem', nav: 'navigation', main: 'main', form: 'form',
    table: 'table', checkbox: 'checkbox', radio: 'radio' };
  return map[role] || role;
}

function buildSelectorCandidates(info) {
  const candidates = [];

  const roleName = info.ariaLabel || info.labelText || info.innerText || info.placeholder || info.value;
  if (roleName && info.role && info.role !== info.tagName) {
    candidates.push({ type: 'role', priority: 1,
      selector: "getByRole('" + normalizeRole(info.role) + "', { name: '" + esc(roleName.slice(0,50)) + "' })",
      playwrightCode: "page.getByRole('" + normalizeRole(info.role) + "', { name: '" + esc(roleName.slice(0,50)) + "' })",
      description: 'ロールベース（最推奨）' });
  }
  if (info.labelText) {
    candidates.push({ type: 'label', priority: 2,
      selector: "getByLabel('" + esc(info.labelText) + "')",
      playwrightCode: "page.getByLabel('" + esc(info.labelText) + "')",
      description: 'ラベルテキストベース' });
  }
  if (info.placeholder) {
    candidates.push({ type: 'placeholder', priority: 3,
      selector: "getByPlaceholder('" + esc(info.placeholder) + "')",
      playwrightCode: "page.getByPlaceholder('" + esc(info.placeholder) + "')",
      description: 'プレースホルダーベース' });
  }
  if (info.innerText && info.innerText.length > 0 && info.innerText.length < 60) {
    candidates.push({ type: 'text', priority: 4,
      selector: "getByText('" + esc(info.innerText) + "')",
      playwrightCode: "page.getByText('" + esc(info.innerText) + "', { exact: true })",
      description: 'テキストベース' });
  }
  Object.entries(info.testAttrs).forEach(([attr, val]) => {
    if (attr === 'data-testid') {
      candidates.push({ type: 'testid', priority: 5,
        selector: "getByTestId('" + esc(val) + "')",
        playwrightCode: "page.getByTestId('" + esc(val) + "')",
        description: attr + ' ベース' });
    } else {
      candidates.push({ type: 'testid', priority: 5,
        selector: '[' + attr + '="' + val + '"]',
        playwrightCode: "page.locator('[" + attr + '="' + val + '"]\')',
        description: attr + ' ベース' });
    }
  });
  if (info.id) {
    candidates.push({ type: 'id', priority: 6,
      selector: '#' + info.id,
      playwrightCode: "page.locator('#" + info.id + "')",
      description: 'ID ベース' });
  }
  if (info.ariaLabel && !candidates.some(c => c.playwrightCode.includes(info.ariaLabel))) {
    candidates.push({ type: 'aria', priority: 7,
      selector: '[aria-label="' + info.ariaLabel + '"]',
      playwrightCode: 'page.locator(\'[aria-label="' + info.ariaLabel + '"]\')',
      description: 'aria-label ベース' });
  }
  if (info.name) {
    candidates.push({ type: 'name', priority: 8,
      selector: info.tagName + '[name="' + info.name + '"]',
      playwrightCode: "page.locator('" + info.tagName + '[name="' + info.name + '"]\')',
      description: 'name属性ベース' });
  }
  if (info.classes.length > 0) {
    const cs = info.tagName + '.' + info.classes.slice(0, 2).join('.');
    candidates.push({ type: 'class', priority: 9,
      selector: cs, playwrightCode: "page.locator('" + cs + "')", description: 'クラスベース（注意）' });
  }
  candidates.push({ type: 'xpath', priority: 10,
    selector: info.xpath, playwrightCode: "page.locator('xpath=" + info.xpath + "')",
    description: 'XPath（最終手段）' });

  return candidates.sort((a, b) => a.priority - b.priority);
}

async function checkSelectorCounts(candidates, pageInstance) {
  const results = [];
  for (const cand of candidates) {
    let count = 0, error = null;
    try {
      if (cand.type === 'role') {
        const m = cand.playwrightCode.match(/getByRole\('([^']+)',\s*\{[^}]*name:\s*'([^']+)'/);
        if (m) count = await pageInstance.getByRole(m[1], { name: m[2] }).count();
      } else if (cand.type === 'label') {
        const m = cand.playwrightCode.match(/getByLabel\('([^']+)'\)/);
        if (m) count = await pageInstance.getByLabel(m[1]).count();
      } else if (cand.type === 'placeholder') {
        const m = cand.playwrightCode.match(/getByPlaceholder\('([^']+)'\)/);
        if (m) count = await pageInstance.getByPlaceholder(m[1]).count();
      } else if (cand.type === 'text') {
        const m = cand.playwrightCode.match(/getByText\('([^']+)'/);
        if (m) count = await pageInstance.getByText(m[1], { exact: true }).count();
      } else if (cand.type === 'testid') {
        const m = cand.playwrightCode.match(/getByTestId\('([^']+)'\)/);
        if (m) { count = await pageInstance.getByTestId(m[1]).count(); }
        else {
          const lm = cand.playwrightCode.match(/locator\('([^']+)'\)/);
          if (lm) count = await pageInstance.locator(lm[1]).count();
        }
      } else {
        const lm = cand.playwrightCode.match(/locator\('([^']+)'\)/);
        if (lm) count = await pageInstance.locator(lm[1]).count();
      }
    } catch (e) { error = e.message; }
    results.push({ ...cand, count, error, unique: count === 1 });
  }
  return results;
}

// ============================================================
// API
// ============================================================

app.post('/api/launch', async (req, res) => {
  try {
    const { url, headless } = req.body;
    if (browser) { await browser.close(); browser = null; page = null; }
    browser = await chromium.launch({ headless: headless || false });
    const context = await browser.newContext();
    page = await context.newPage();
    page.on('framenavigated', async (frame) => {
      if (frame === page.mainFrame()) {
        broadcast({ type: 'navigation', url: frame.url() });
        await injectClickListener();
      }
    });
    if (url) await page.goto(url);
    await injectClickListener();
    res.json({ success: true, url: page.url() });
    broadcast({ type: 'status', message: 'ブラウザ起動: ' + page.url() });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

async function injectClickListener() {
  if (!page) return;
  // exposeFunction でブラウザ→Node.js に直接コールバック（fetchより確実）
  try {
    await page.exposeFunction('__pwCapture', async (x, y) => {
      await captureAt(x, y);
    });
  } catch (e) { /* 2回目以降は無視 */ }
  try {
    await page.evaluate(() => {
      if (window.__pwInspectorInjected) return;
      window.__pwInspectorInjected = true;
      document.addEventListener('click', (e) => {
        if (e.altKey || e.ctrlKey) {
          e.preventDefault(); e.stopPropagation();
          const el = e.target;
          el.style.outline = '3px solid #ff6b35';
          setTimeout(() => { el.style.outline = ''; }, 1500);
          window.__pwCapture(e.clientX, e.clientY);
        }
      }, true);
      let lastHovered = null;
      document.addEventListener('mouseover', (e) => {
        if (lastHovered && lastHovered !== e.target) lastHovered.style.outline = '';
        if (e.altKey) { e.target.style.outline = '2px dashed #ff6b35'; lastHovered = e.target; }
      });
    });
  } catch (e) { /* ignore */ }
}

// キャプチャ処理（exposeFunction から呼ばれる）
async function captureAt(x, y) {
  if (!page) return;
  try {
    const elementHandle = await page.evaluateHandle(({ x, y }) => document.elementFromPoint(x, y), { x, y });
    const info = await analyzeElement(elementHandle, page);
    const candidates = buildSelectorCandidates(info);
    const withCounts = await checkSelectorCounts(candidates, page);
    const best = withCounts.find(c => c.unique) || withCounts[0];

    const session = getOrCreateSession(page.url());
    let key = autoKey(info);
    let suffix = 2;
    while (session.elements[key]) { key = autoKey(info) + suffix++; }

    session.elements[key] = {
      key, memo: '',
      best: { type: best.type, code: best.playwrightCode, selector: best.selector, count: best.count },
      candidates: withCounts.map(c => ({
        type: c.type, priority: c.priority, code: c.playwrightCode,
        selector: c.selector, count: c.count, unique: c.unique, description: c.description,
      })),
      tag: info.tagName,
      attrs: { id: info.id, role: info.role, ariaLabel: info.ariaLabel, labelText: info.labelText,
        placeholder: info.placeholder, name: info.name, type: info.type,
        innerText: info.innerText, classes: info.classes, testAttrs: info.testAttrs },
      capturedAt: new Date().toISOString(),
    };

    broadcast({ type: 'element_captured', timestamp: new Date().toISOString(),
      info, candidates: withCounts, bestSelector: best,
      currentUrl: page.url(), sessionKey: key,
      sessionElementCount: Object.keys(session.elements).length });
  } catch (e) {
    broadcast({ type: 'error', message: e.message });
  }
}

app.post('/api/capture-element', async (req, res) => {
  const { x, y } = req.body;
  await captureAt(x, y);
  res.json({ success: true });
});

app.post('/api/update-element', (req, res) => {
  const { oldKey, newKey, memo } = req.body;
  if (!currentSession || !currentSession.elements[oldKey])
    return res.status(404).json({ error: 'element not found' });
  const el = currentSession.elements[oldKey];
  if (newKey && newKey !== oldKey) {
    if (currentSession.elements[newKey]) return res.status(400).json({ error: 'キー名が重複しています' });
    el.key = newKey;
    currentSession.elements[newKey] = el;
    delete currentSession.elements[oldKey];
  }
  if (memo !== undefined) el.memo = memo;
  res.json({ success: true });
  broadcast({ type: 'session_updated', elementCount: Object.keys(currentSession.elements).length });
});

app.delete('/api/element/:key', (req, res) => {
  if (currentSession && currentSession.elements[req.params.key]) {
    delete currentSession.elements[req.params.key];
    broadcast({ type: 'session_updated', elementCount: Object.keys(currentSession.elements).length });
  }
  res.json({ success: true });
});

app.get('/api/session', (req, res) => { res.json({ session: currentSession }); });

app.post('/api/session/reset', (req, res) => {
  currentSession = null;
  res.json({ success: true });
  broadcast({ type: 'session_reset' });
});

app.get('/api/export/json', (req, res) => {
  if (!currentSession) return res.status(400).json({ error: 'セッションがありません' });
  const filename = currentSession.name + '-selectors.json';
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Content-Disposition', 'attachment; filename="' + filename + '"');
  res.send(JSON.stringify(buildExportJSON(currentSession), null, 2));
});

app.get('/api/export/js', (req, res) => {
  if (!currentSession) return res.status(400).json({ error: 'セッションがありません' });
  const filename = currentSession.name + '-selectors.js';
  res.setHeader('Content-Type', 'text/javascript');
  res.setHeader('Content-Disposition', 'attachment; filename="' + filename + '"');
  res.send(buildExportJS(currentSession));
});

app.post('/api/export/save', (req, res) => {
  const { outputDir, format } = req.body;
  if (!currentSession) return res.status(400).json({ error: 'セッションがありません' });
  try {
    const dir = outputDir || path.join(process.cwd(), 'selectors');
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const savedFiles = [];
    if (!format || format === 'json' || format === 'both') {
      const p = path.join(dir, currentSession.name + '-selectors.json');
      fs.writeFileSync(p, JSON.stringify(buildExportJSON(currentSession), null, 2), 'utf8');
      savedFiles.push(p);
    }
    if (!format || format === 'js' || format === 'both') {
      const p = path.join(dir, currentSession.name + '-selectors.js');
      fs.writeFileSync(p, buildExportJS(currentSession), 'utf8');
      savedFiles.push(p);
    }
    res.json({ success: true, files: savedFiles });
    broadcast({ type: 'status', message: '保存: ' + savedFiles.join(', ') });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post('/api/check-selector', async (req, res) => {
  if (!page) return res.status(400).json({ error: 'ブラウザが起動していません' });
  const { selector } = req.body;
  try {
    const count = await page.locator(selector).count();
    res.json({ count, unique: count === 1 });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.get('/api/status', (req, res) => {
  res.json({
    browserOpen: !!browser,
    currentUrl: page ? page.url() : null,
    elementCount: currentSession ? Object.keys(currentSession.elements).length : 0,
  });
});

app.post('/api/close', async (req, res) => {
  if (browser) { await browser.close(); browser = null; page = null; }
  res.json({ success: true });
  broadcast({ type: 'status', message: 'ブラウザを閉じました' });
});

wss.on('connection', (ws) => {
  clients.add(ws);
  ws.on('close', () => clients.delete(ws));
});

function broadcast(data) {
  const msg = JSON.stringify(data);
  clients.forEach(ws => { if (ws.readyState === WebSocket.OPEN) ws.send(msg); });
}

const PORT = 3737;
server.listen(PORT, () => {
  console.log('\n🎯 Playwright Inspector 起動中');
  console.log('📡 http://localhost:' + PORT + '\n');
});
