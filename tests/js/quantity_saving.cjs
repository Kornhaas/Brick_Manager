// Run with: node --test tests/js/quantity_saving.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const source = readFileSync('brick_manager/static/js/set_maintenance.js', 'utf8');

function node(tag = 'span') {
  return {
    tagName: tag.toUpperCase(), children: [], attributes: {}, className: '', textContent: '', hidden: false,
    append(...items) { this.children.push(...items); },
    setAttribute(name, value) { this.attributes[name] = value; },
    getAttribute(name) { return this.attributes[name] ?? null; },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener(name, callback) { this[name] = callback; },
    querySelector(selector) { return this.children.find(child => child.className?.split(' ').includes(selector.slice(1))) || null; },
  };
}
function setup() {
  const requests = [], timers = [], listeners = {};
  const document = { addEventListener(name, callback) { (listeners[name] ||= []).push(callback); }, querySelectorAll: () => [], createElement: node };
  const context = vm.createContext({ document, setTimeout: callback => timers.push(callback), console: { log() {}, error() {} }, fetch(url, options) {
    return new Promise((resolve, reject) => requests.push({ payload: JSON.parse(options.body), resolve, reject }));
  } });
  vm.runInContext(source, context);
  function input(value = '2', id = '42') {
    const parent = node('td'), row = { className: '' };
    return Object.assign(node('input'), { value, max: '10', style: {}, dataset: {}, parentElement: parent,
      getAttribute(name) { return ({ 'data-part-id': id, 'data-part-type': 'regular' })[name] ?? this.attributes[name] ?? null; },
      closest() { return row; }, setCustomValidity(message) { this.validationMessage = message; },
    });
  }
  function resolve(index, value) { requests[index].resolve({ ok: true, json: async () => ({ success: true, have_quantity: value, total_quantity: 10 }) }); }
  return { context, requests, timers, input, resolve, document, listeners };
}
const settle = () => new Promise(resolve => setImmediate(resolve));

test('writes to one part are serialized and the newest edit wins', async () => {
  const s = setup(), input = s.input();
  const first = s.context.saveQuantity(input);
  input.value = '7'; const second = s.context.saveQuantity(input);
  assert.equal(s.requests.length, 1, 'a second write must wait for the first');
  s.resolve(0, 2); await settle();
  assert.equal(input.value, '7', 'an old response must not overwrite the newer edit');
  assert.equal(s.requests.length, 2);
  assert.equal(s.requests[1].payload.have_quantity, 7);
  s.resolve(1, 7);
  assert.equal(await first, true); assert.equal(await second, true);
  assert.equal(input.value, '7'); assert.equal(input.dataset.lastSavedValue, '7');
});

test('intermediate pending edits are coalesced without dropping the last intention', async () => {
  const s = setup(), input = s.input();
  const result = s.context.saveQuantity(input);
  input.value = '3'; s.context.saveQuantity(input);
  input.value = '9'; s.context.saveQuantity(input);
  assert.equal(s.requests.length, 1);
  s.resolve(0, 2); await settle();
  assert.equal(s.requests[1].payload.have_quantity, 9);
  s.resolve(1, 9); assert.equal(await result, true);
  assert.equal(s.requests.length, 2); assert.equal(input.value, '9');
});

test('duplicate Enter/key events do not duplicate writes or focus movement', async () => {
  const s = setup(), input = s.input(); let moves = 0;
  s.context.focusAdjacentQuantityInput = () => { moves++; };
  s.context.saveAndMoveFromQuantityInput(input);
  s.context.saveAndMoveFromQuantityInput(input);
  assert.equal(s.requests.length, 1);
  s.resolve(0, 2); await settle();
  assert.equal(moves, 1);
});

test('different parts can save independently', async () => {
  const s = setup(), a = s.input('2', '1'), b = s.input('4', '2');
  const first = s.context.saveQuantity(a), second = s.context.saveQuantity(b);
  assert.equal(s.requests.length, 2);
  s.resolve(1, 4); s.resolve(0, 2);
  assert.equal(await first, true); assert.equal(await second, true);
});

test('invalid, fractional and out-of-range quantities never reach the backend', async () => {
  for (const value of ['1.9', '', '-1', '11', 'Infinity', '9007199254740993']) {
    const s = setup(), input = s.input(value);
    const result = s.context.saveQuantity(input);
    assert.equal(s.requests.length, 0, value);
    assert.equal(await result, false, value);
    assert.equal(input.getAttribute('aria-invalid'), 'true', value);
    assert.ok(input.parentElement.querySelector('.quantity-save-status').textContent, value);
  }
});

test('a response does not erase newer typing before its change event', async () => {
  const s = setup(), input = s.input();
  const pending = s.context.saveQuantity(input);
  input.value = '7'; s.resolve(0, 2);
  assert.equal(await pending, false);
  assert.equal(input.value, '7');
  const next = s.context.saveQuantity(input); s.resolve(1, 7);
  assert.equal(await next, true); assert.equal(input.dataset.lastSavedValue, '7');
});

test('network failures stay visible and the unchanged value can be retried', async () => {
  const s = setup(), input = s.input('3');
  const pending = s.context.saveQuantity(input); s.requests[0].reject(new Error('offline'));
  assert.equal(await pending, false);
  const status = input.parentElement.querySelector('.quantity-save-status');
  assert.match(status.textContent, /nicht gespeichert/i);
  for (const callback of s.timers) callback();
  assert.match(status.textContent, /nicht gespeichert/i);
  const retry = input.parentElement.querySelector('.quantity-save-retry');
  assert.equal(retry.hidden, false); retry.click();
  assert.equal(s.requests.length, 2);
  s.resolve(1, 3); await settle();
  assert.equal(input.dataset.lastSavedValue, '3'); assert.equal(retry.hidden, true);
});

test('failure of an older write does not discard a newer queued value', async () => {
  const s = setup(), input = s.input();
  const pending = s.context.saveQuantity(input); input.value = '7'; s.context.saveQuantity(input);
  s.requests[0].reject(new Error('offline')); await settle();
  assert.equal(s.requests.length, 2); assert.equal(s.requests[1].payload.have_quantity, 7);
  s.resolve(1, 7); assert.equal(await pending, true); assert.equal(input.value, '7');
});

test('HTTP failure cannot be mistaken for a successful save', async () => {
  const s = setup(), input = s.input();
  const pending = s.context.saveQuantity(input);
  s.requests[0].resolve({ ok: false, json: async () => ({ success: true, have_quantity: 2, total_quantity: 10 }) });
  assert.equal(await pending, false);
  assert.match(input.parentElement.querySelector('.quantity-save-status').textContent, /nicht gespeichert/i);
});


test('recreated inputs for the same logical part still share one write queue', async () => {
  const s = setup(), oldInput = s.input('2'), newInput = s.input('7');
  const result = s.context.saveQuantity(oldInput); s.context.saveQuantity(newInput);
  assert.equal(s.requests.length, 1);
  s.resolve(0, 2); await settle();
  assert.equal(newInput.value, '7'); assert.equal(s.requests[1].payload.have_quantity, 7);
  s.resolve(1, 7); assert.equal(await result, true);
  assert.equal(newInput.dataset.lastSavedValue, '7');
});

test('explicit bulk submission waits for pending writes and captures the latest form value', async () => {
  const s = setup(), input = s.input('2'), submitter = { disabled: false, matches: () => false };
  let submitted = 0;
  const form = { dataset: {}, closest: () => ({}), querySelectorAll: () => [input], querySelector: () => null, requestSubmit() { submitted++; } };
  s.document.activeElement = submitter;
  s.context.saveQuantity(input); input.value = '7';
  const event = { target: form, submitter, prevented: false, preventDefault() { this.prevented = true; }, stopPropagation() {} };
  s.listeners.submit[0](event);
  assert.equal(event.prevented, true); assert.equal(submitted, 0); assert.equal(submitter.disabled, true);
  assert.equal(s.requests.length, 1);
  s.resolve(0, 2); await settle();
  assert.equal(s.requests[1].payload.have_quantity, 7); assert.equal(submitted, 0);
  s.resolve(1, 7); await settle();
  assert.equal(submitted, 1); assert.equal(submitter.disabled, false);
});

test('failed quantity save keeps bulk submission on the editable page', async () => {
  const s = setup(), input = s.input('2'), submitter = { disabled: false, matches: () => false };
  let submitted = 0;
  const form = { dataset: {}, closest: () => ({}), querySelectorAll: () => [input], querySelector: () => null, requestSubmit() { submitted++; } };
  s.document.activeElement = submitter;
  s.context.saveQuantity(input);
  s.listeners.submit[0]({ target: form, submitter, preventDefault() {}, stopPropagation() {} });
  s.requests[0].reject(new Error('offline')); await settle();
  assert.equal(submitted, 0); assert.equal(submitter.disabled, false);
  assert.match(input.parentElement.querySelector('.quantity-save-status').textContent, /nicht gespeichert/i);
});


test('bulk completion cannot submit a different set opened while its save was pending', async () => {
  const s = setup(), input = s.input('2'), submitter = { disabled: false, matches: () => false };
  let submitted = 0;
  const hidden = { value: 'old-set' };
  const form = { dataset: {}, closest: () => ({}), querySelectorAll: () => [input], querySelector: () => hidden, requestSubmit() { submitted++; } };
  s.document.activeElement = submitter;
  s.context.saveQuantity(input);
  s.listeners.submit[0]({ target: form, submitter, preventDefault() {}, stopPropagation() {} });
  hidden.value = 'different-set';
  s.resolve(0, 2); await settle();
  assert.equal(submitted, 0);
});
