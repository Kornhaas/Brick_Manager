// Run with: node --test tests/js/set_details_rendering.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const source = readFileSync('brick_manager/static/js/set_maintenance.js', 'utf8');
// Exercise the actual asynchronous view-details renderer with catalog responses.
const prefix = source.slice(0, source.indexOf('document.addEventListener("DOMContentLoaded"'));
const start = source.indexOf('document.querySelectorAll(".view-details").forEach');
const renderer = source.slice(start, source.indexOf('  // Handle back to sets button', start));

async function render(minifig) {
  const elements = new Map(); let clicked;
  const element = id => {
    if (!elements.has(id)) elements.set(id, { innerHTML: '', value: '', classList: { remove() {}, add() {} } });
    return elements.get(id);
  };
  const button = { getAttribute: () => '42', addEventListener(name, callback) { clicked = callback; } };
  const context = vm.createContext({
    document: { querySelectorAll: () => [button], getElementById: element },
    setDetails: element('set-details'), setsTable: element('sets-table'), window: { scrollTo() {} },
    attachAutoSaveListeners() {}, console: { error(error) { throw error; } },
    fetch: async () => ({ json: async () => ({ parts: [], minifigs: [minifig], status: 'unknown' }) }),
  });
  vm.runInContext(prefix + renderer, context); clicked();
  await new Promise(resolve => setImmediate(resolve));
  return element('minifigs-table-body').innerHTML;
}

test('minifigure names and identifiers remain text in both row and nested heading', async () => {
  const html = await render({ fig_num: '<figure & "1">', name: '<img src=x onerror="alert(1)">', quantity: 1,
    img_url: '', parts: [{ id: 1, part_num: 'p', name: 'Part', color: 'Red', color_rgb: 'FF0000', quantity: 1, have_quantity: 0 }] });
  assert.ok(html.includes('&lt;figure &amp; &quot;1&quot;&gt;'));
  assert.ok(html.includes('Parts for &lt;img src=x onerror=&quot;alert(1)&quot;&gt;'));
  assert.equal(html.includes('<img src=x onerror="alert(1)">'), false);
});

test('nested minifigure part labels, colors and locations are escaped consistently', async () => {
  const html = await render({ fig_num: 'fig', name: 'Figure', quantity: 1, img_url: '', parts: [{
    id: 1, part_num: '<part>', name: 'A & B <tile>', color: '<red>', color_rgb: 'FF0000',
    location: '<shelf>', quantity: 1, have_quantity: 0,
  }] });
  for (const text of ['&lt;part&gt;', 'A &amp; B &lt;tile&gt;', '&lt;red&gt;', '&lt;shelf&gt;']) assert.ok(html.includes(text), text);
  for (const markup of ['<part>', '<tile>', '<red>', '<shelf>']) assert.equal(html.includes(markup), false, markup);
});

test('a malformed catalog color cannot introduce attributes into the row style', async () => {
  const html = await render({ fig_num: 'fig', name: 'Figure', quantity: 1, img_url: '', parts: [{
    id: 1, part_num: 'p', name: 'Part', color: 'Red', color_rgb: 'FFFFFF" onclick="alert(1)', quantity: 1, have_quantity: 0,
  }] });
  assert.equal(html.includes('onclick="alert(1)'), false);
  assert.ok(html.includes('background-color: #FFFFFF;'));
});
