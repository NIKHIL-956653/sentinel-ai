// End-to-end UI test. Runs the real app in DEMO_MODE (no keys, no network, in-memory store) and
// drives every screen with Playwright. Run locally:
//   DEMO_MODE=true EXPENSIVE_LIMIT_PER_MINUTE=100 python -m uvicorn api.main:app --port 8765 &   # then
//   node tests/e2e/ui.spec.js
// CI does the same (see .github/workflows/ci.yml). Leaflet/tiles are stubbed so no CDN is needed.
const { chromium } = require('playwright');
const BASE = process.env.E2E_BASE || 'http://127.0.0.1:8765';
const SHOTS = process.env.E2E_SHOTS || '';           // directory for screenshots (optional)
const fs = require('fs');
if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });

const LEAFLET_STUB = 'window.L={map:()=>({invalidateSize(){},on(){}}),tileLayer:()=>({addTo(){return this},setUrl(){}}),' +
  'layerGroup:()=>({addTo(){return this},clearLayers(){}}),circleMarker:()=>({addTo(){return this},bindPopup(){return this}})};';

function assert(cond, msg) { if (!cond) throw new Error('ASSERT: ' + msg); }

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !/429|503/.test(m.text())) errors.push('CONSOLE ' + m.text()); });
  await page.route(/cartocdn/, r => r.abort());
  await page.route(/leaflet\.min\.js/, r => r.fulfill({ contentType: 'application/javascript', body: LEAFLET_STUB }));
  await page.route(/leaflet\.min\.css/, r => r.fulfill({ contentType: 'text/css', body: '' }));
  const shot = name => SHOTS ? page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: true }) : Promise.resolve();

  // 1. deep link → news search streams through the pipeline HUD
  await page.goto(`${BASE}/app/#/news?q=Northland%20Karim`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#mainApp', { state: 'visible', timeout: 15000 });
  assert(await page.isVisible('#demoBanner'), 'demo banner visible in DEMO_MODE');
  await page.waitForSelector('#newsResults .news-card', { timeout: 30000 });
  const stages = await page.$$eval('#pipelineStages li.done', els => els.length);
  assert(stages >= 7, `pipeline HUD marked stages done (${stages})`);
  assert((await page.$$('.claim.corroborated')).length >= 1, 'a corroborated claim rendered');
  assert((await page.$$('.claim.disputed')).length >= 1, 'a disputed claim rendered');
  assert((await page.$$('.chip')).length >= 3, 'entity chips rendered');
  assert((await page.$$('.contra')).length >= 1, 'contradiction rendered');
  assert((await page.textContent('#newsResults')).includes('Kharkiv'), 'city-precision geotag shown');
  await shot('1-news');

  // 2. second run of the same query (cache miss via different casing is still a hit → use another query) → timeline needs 2 runs
  await page.evaluate(async () => { await fetch('/api/v1/news', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: 'Northland Karim' }) }); });
  // timeline appears only with ≥2 runs; in demo the 1h cache makes the 2nd call a hit, so just assert the endpoint answers
  const tl = await page.evaluate(async () => (await fetch('/api/v1/news/timeline?q=Northland%20Karim')).json());
  assert(tl.runs.length >= 1 && tl.stories.length >= 1, 'timeline endpoint returns archived run');

  // 3. brief
  await page.click('.nav-btn[data-screen="brief"]');
  await page.waitForSelector('.brief-head', { timeout: 20000 });
  assert((await page.textContent('.brief-head')).length > 10, 'brief headline');
  assert((await page.$$('.brief-sec .ref')).length >= 1, 'brief cites stories');
  await shot('2-brief');

  // 4. graph
  await page.click('.nav-btn[data-screen="graph"]');
  await page.waitForFunction(() => /stories/.test(document.getElementById('graphMeta').textContent), null, { timeout: 15000 });
  assert(!/0 stories/.test(await page.textContent('#graphMeta')), 'graph has stories');
  await shot('3-graph');

  // 5. sources (reliability)
  await page.click('.nav-btn[data-screen="sources"]');
  await page.waitForSelector('.src-table', { timeout: 15000 });
  assert((await page.$$('.src-table tr')).length >= 3, 'reliability rows');
  await shot('4-sources');

  // 6. country dossier via hash + export
  await page.goto(`${BASE}/app/#/countries/India`);
  await page.waitForSelector('#countryResults .panel', { timeout: 20000 });
  assert((await page.textContent('#countryResults')).includes('INDIA'), 'dossier rendered');
  const md = await page.evaluate(async () => (await fetch('/api/v1/export/country/India')).text());
  assert(md.startsWith('# India'), 'country export markdown');
  await shot('5-country');

  // 7. theme + palette → compare
  await page.click('#themeBtn');
  assert(await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === 'light', 'light theme');
  await page.keyboard.press('Control+K');
  await page.type('#paletteInput', 'compare india pak');
  await page.keyboard.press('Enter');
  await page.waitForSelector('#compareResults .grid-2', { timeout: 30000 });
  assert(await page.evaluate(() => location.hash) === '#/compare/India/Pakistan', 'compare deep link');
  await shot('6-compare-light');

  // 8. health / metrics / security headers
  const health = await page.evaluate(async () => (await fetch('/api/v1/health')).json());
  assert(health.demo_mode === true && health.rate_limiter === 'memory', 'health reports demo + limiter');
  const hdrs = await page.evaluate(async () => { const r = await fetch('/api/v1/health'); return [r.headers.get('x-content-type-options'), r.headers.get('x-request-id')]; });
  assert(hdrs[0] === 'nosniff' && hdrs[1], 'security headers + request id');
  const metrics = await page.evaluate(async () => (await fetch('/metrics')).text());
  assert(metrics.includes('sentinel_llm_calls_total'), 'prometheus metrics');

  await browser.close();
  if (errors.length) { console.error(errors); process.exit(1); }
  console.log('E2E OK');
})().catch(e => { console.error(e); process.exit(1); });
