// Run with: node --test tests/js/quantity_navigation.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const source = readFileSync('brick_manager/static/js/set_maintenance.js', 'utf8');
const listeners = {};
const context = vm.createContext({
  document: {
    addEventListener: (name, callback) => { listeners[name] = callback; },
    querySelectorAll: () => [],
  },
  console: { log() {} },
});
vm.runInContext(source, context);

function setup(options = [{}, {}, {}]) {
  let focused;
  const details = { querySelectorAll: () => inputs };
  const inputs = options.map(option => ({
    matches: () => true,
    closest: () => details,
    getClientRects: () => option.hidden ? [] : [{}],
    focus() { focused = this; },
    ...option,
  }));
  function press(index, extra = {}) {
    const event = {
      key: 'Tab', target: inputs[index], prevented: false,
      preventDefault() { this.prevented = true; }, ...extra,
    };
    listeners.keydown(event);
    return { prevented: event.prevented, focused };
  }
  return { inputs, press };
}

test('Tab moves forward and Shift+Tab backward', () => {
  const { inputs, press } = setup();
  assert.equal(press(0).focused, inputs[1]);
  assert.equal(press(2, { shiftKey: true }).focused, inputs[1]);
});

test('hidden, disabled and read-only quantities are skipped', () => {
  const { inputs, press } = setup([{}, { hidden: true }, { disabled: true }, { readOnly: true }, {}]);
  assert.equal(press(0).focused, inputs[4]);
  assert.equal(press(4, { shiftKey: true }).focused, inputs[0]);
});

test('native navigation remains at both ends', () => {
  const { press } = setup();
  assert.equal(press(0, { shiftKey: true }).prevented, false);
  assert.equal(press(2).prevented, false);
});

test('other keys, shortcuts and unrelated controls are untouched', () => {
  for (const extra of [
    { key: 'Enter' }, { ctrlKey: true }, { altKey: true },
    { metaKey: true }, { isComposing: true },
    { target: { matches: () => false } },
    { target: { matches: () => true, closest: () => null } },
  ]) {
    assert.equal(setup().press(0, extra).prevented, false);
  }
});
