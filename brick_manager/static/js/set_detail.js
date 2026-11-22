(() => {
  const form = document.getElementById('set-detail-form');
  const byId = id => document.getElementById(id);
  const fields = Array.from(form.querySelectorAll('[data-saved]'));
  const quantities = fields.filter(field => field.hasAttribute('data-required'));
  const rows = quantities.map(input => ({
    input,
    row: input.closest('[data-part-row]'),
    search: input.closest('[data-part-row]').dataset.search.toLocaleLowerCase()
  }));
  const state = byId('detail-save-state');
  const saveButton = byId('save-detail');
  const retry = byId('retry-detail');
  const search = byId('part-search');
  const mismatch = byId('filter-mismatched-parts');
  const colorGroups = Array.from(form.querySelectorAll('[data-color-group]')).map(group => ({
    group, rows: rows.filter(({ row }) => row.closest('[data-color-group]') === group)
  }));
  const leave = byId('leave-dialog');
  const bulk = byId('bulk-dialog');
  const back = byId('set-back-link');
  const uncertain = new Set();
  let pending = null;
  let pendingBulkValue;
  let leaving = false;
  let pinnedInput = null;
  form.noValidate = true;
  byId('set-detail').addEventListener('click', event => {
    const button = event.target.closest('.image-preview');
    if (!button) return;
    byId('preview-title').textContent = button.dataset.imageName;
    byId('preview-image').src = button.querySelector('img').src;
    byId('image-dialog').showModal();
  });
  byId('close-image').addEventListener('click', () => byId('image-dialog').close());

  function changed(field) {
    return field.value !== field.dataset.saved || uncertain.has(field.name);
  }
  function preventDraftLoss(event) {
    event.preventDefault();
    event.returnValue = '';
  }
  function indicate(value, message) {
    state.dataset.state = value;
    state.textContent = message;
    retry.hidden = value !== 'error';
    saveButton.setAttribute('aria-disabled', String(value === 'saving'));
    form.setAttribute('aria-busy', String(value === 'saving'));
    if (value === 'saving' || fields.some(changed)) window.addEventListener('beforeunload', preventDraftLoss);
    else window.removeEventListener('beforeunload', preventDraftLoss);
    byId('discard-and-back').disabled = value === 'saving';
  }
  function indicateDraft() {
    if (pending) return;
    if (fields.some(changed)) indicate('dirty', 'Ungespeicherte Änderungen');
    else indicate('clean', 'Keine offenen Änderungen.');
  }
  function fieldError(field, message = '') {
    byId('error-' + field.name).textContent = message;
    if (message) field.setAttribute('aria-invalid', 'true');
    else field.removeAttribute('aria-invalid');
  }

  function quantityState(input) {
    if (!/^\d+$/.test(input.value) || !input.validity.valid) return 'invalid';
    return Number(input.value) === Number(input.dataset.required) ? 'complete' : 'missing';
  }
  function updateQuantityVisuals() {
    for (const { input, row } of rows) {
      const value = quantityState(input);
      row.dataset.quantityState = value;
      row.querySelector('[data-quantity-label]').textContent = value === 'complete' ? '✓ Vollständig'
        : value === 'invalid' ? 'Eingabe prüfen'
        : Number(input.dataset.required) - Number(input.value) + ' fehlen';
    }
    for (const { group, rows: items } of colorGroups) {
      const complete = items.filter(({ input }) => quantityState(input) === 'complete').length;
      group.querySelector('[data-color-progress]').textContent = complete + ' von ' + items.length + ' vollständig';
    }
  }
  function filterRows(keep = null, revealMatches = false) {
    const needle = search.value.trim().toLocaleLowerCase();
    let matches = 0;
    pinnedInput = null;
    for (const { input, row, search: terms } of rows) {
      const match = terms.includes(needle) && (!mismatch.checked || quantityState(input) !== 'complete');
      if (match) matches++;
      if (!match && input === keep) pinnedInput = input;
      row.hidden = !match && input !== keep;
    }
    for (const { group, rows: items } of colorGroups) {
      group.hidden = items.every(({ row }) => row.hidden);
      if (revealMatches && !group.hidden) {
        for (let parent = group; parent && parent !== form; parent = parent.parentElement) {
          if (parent.tagName === 'DETAILS') parent.open = true;
        }
      }
    }
    byId('part-filter-result').textContent = (needle || mismatch.checked)
      ? matches + ' von ' + rows.length + ' Teilezeilen passen.' + (pinnedInput ? ' Die aktuelle Zeile bleibt bis zum Feldwechsel sichtbar.' : '')
      : '';
  }
  search.addEventListener('input', () => filterRows(null, true));
  for (const type of ['keydown', 'keypress']) {
    search.addEventListener(type, event => {
      if (event.key === 'Enter' && !event.isComposing) event.preventDefault();
    });
  }
  mismatch.addEventListener('change', () => filterRows(null, true));
  byId('color-group-actions').hidden = false;
  for (const [id, open] of [['collapse-colors', false], ['expand-colors', true]]) {
    byId(id).addEventListener('click', () => {
      for (const { group } of colorGroups) {
        group.open = open;
        if (open) {
          for (let parent = group.parentElement; parent && parent !== form; parent = parent.parentElement) {
            if (parent.tagName === 'DETAILS') parent.open = true;
          }
        }
      }
    });
  }
  form.addEventListener('focusin', event => {
    if (pinnedInput && event.target !== pinnedInput && !event.target.closest('.save-bar')) filterRows();
  });
  function editField(event) {
    if (!event.target.hasAttribute('data-saved')) return;
    fieldError(event.target);
    updateQuantityVisuals();
    indicateDraft();
  }
  form.addEventListener('input', editField);
  form.addEventListener('change', editField);

  function revealError(field) {
    const row = field.closest('[data-part-row]');
    if (row) {
      for (let parent = row.parentElement; parent && parent !== form; parent = parent.parentElement) {
        if (parent.tagName === 'DETAILS') parent.open = true;
      }
      filterRows(field);
    }
    field.focus();
  }
  function validatedDraft() {
    const draft = {};
    let firstInvalid;
    for (const field of fields) {
      if (!changed(field)) continue;
      if (field.hasAttribute('data-required') && (!/^\d+$/.test(field.value) || !field.validity.valid)) {
        fieldError(field, 'Ganze Menge zwischen 0 und ' + field.dataset.required + ' eingeben.');
        firstInvalid ??= field;
      } else {
        fieldError(field);
        draft[field.name] = field.name === 'status' ? field.value : Number(field.value);
      }
    }
    if (firstInvalid) {
      indicate('error', 'Speichern fehlgeschlagen – markierte Eingaben prüfen.');
      revealError(firstInvalid);
      return null;
    }
    return draft;
  }
  function refreshProgress(percentage) {
    if (!Number.isFinite(percentage)) {
      const owned = quantities.reduce((sum, input) => sum + Number(input.dataset.saved), 0);
      const required = quantities.reduce((sum, input) => sum + Number(input.dataset.required), 0);
      percentage = required ? owned / required * 100 : 0;
    }
    byId('detail-progress').textContent = percentage.toLocaleString('de', { maximumFractionDigits: 2 }) + ' %';
  }
  async function submitDraft(draft) {
    indicate('saving', 'Wird gespeichert …');
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(draft)
      });
      const data = await response.json();
      if (!response.ok || !data.success) {
        for (const [name, message] of Object.entries(data.field_errors || {})) {
          const field = form.elements.namedItem(name);
          if (field?.hasAttribute('data-saved')) fieldError(field, message);
        }
        throw new Error(data.error || 'Die Anfrage wurde nicht bestätigt.');
      }
      const entries = Object.entries(draft);
      if (entries.some(([key, value]) => data.values?.[key] !== value)) {
        throw new Error('Die Bestätigung enthält abweichende Werte.');
      }
      for (const [key, value] of entries) {
        const field = form.elements.namedItem(key);
        if (key !== 'status' && field.value.trim() && Number(field.value) === value) field.value = String(value);
        field.dataset.saved = String(value);
        uncertain.delete(key);
      }
      const active = document.activeElement;
      const anchor = active?.hasAttribute('data-required') ? active : null;
      const before = anchor?.getBoundingClientRect().top;
      refreshProgress(data.completeness_percentage);
      updateQuantityVisuals();
      filterRows(anchor);
      if (anchor) window.scrollBy(0, anchor.getBoundingClientRect().top - before);
      if (fields.some(changed)) {
        indicate('dirty', 'Ungespeicherte Änderungen');
        return false;
      }
      indicate('saved', 'Alle Änderungen gespeichert');
      return true;
    } catch (error) {
      // A lost response can follow a committed write. Retry the displayed values.
      Object.keys(draft).forEach(name => uncertain.add(name));
      indicate('error', 'Speichern fehlgeschlagen – Eingaben bleiben erhalten. ' + error.message);
      const invalid = fields.find(field => field.getAttribute('aria-invalid') === 'true');
      if (invalid) revealError(invalid);
      return false;
    }
  }
  function save() {
    if (pending) return pending;
    const draft = validatedDraft();
    if (!draft) return Promise.resolve(false);
    if (!Object.keys(draft).length) {
      indicate('saved', 'Alle Änderungen gespeichert');
      return Promise.resolve(true);
    }
    pending = submitDraft(draft).finally(() => { pending = null; });
    return pending;
  }
  for (const button of [saveButton, retry]) {
    button.addEventListener('pointerdown', event => {
      if (document.activeElement?.hasAttribute('data-required')) event.preventDefault();
    });
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    const active = document.activeElement;
    if (!event.submitter && active === search) return;
    if (!event.submitter && active?.hasAttribute('data-required')) advanceQuantity(active, false);
    else save();
  });
  retry.addEventListener('click', () => {
    if (document.activeElement === retry) saveButton.focus({ preventScroll: true });
    save();
  });

  async function advanceQuantity(input, backwards) {
    if (pending) return;
    const index = quantities.indexOf(input);
    const candidates = backwards ? quantities.slice(0, index).reverse() : quantities.slice(index + 1);
    if (await save() && document.activeElement === input) {
      const next = candidates.find(field => field.getClientRects().length);
      if (next) { next.focus(); next.select(); }
    }
  }
  let enteredOnKeyDown = false;
  function handleEnter(event) {
    const input = event.target;
    if (event.isComposing || !input.hasAttribute('data-required') ||
        !(event.key === 'Enter' || event.keyCode === 13 || event.code === 'NumpadEnter')) return;
    event.preventDefault();
    // WebKit can expose only keypress on the touch keyboard.
    if (event.repeat || (event.type === 'keypress' && enteredOnKeyDown)) return;
    enteredOnKeyDown = event.type === 'keydown';
    advanceQuantity(input, event.shiftKey);
  }
  form.addEventListener('keydown', handleEnter);
  form.addEventListener('keypress', handleEnter);
  form.addEventListener('keyup', () => { enteredOnKeyDown = false; });

  function previewBulk(complete) {
    pendingBulkValue = complete;
    const count = kind => rows.filter(({ row }) => row.dataset.kind === kind).length;
    const hidden = rows.filter(({ input }) => !input.getClientRects().length).length;
    byId('bulk-title').textContent = complete ? 'Alle Mengen auf Soll setzen?' : 'Alle Mengen auf 0 setzen?';
    byId('bulk-scope').textContent = 'Box ' + byId('set-detail').dataset.boxId + ' · ' +
      count('regular') + ' reguläre Teilezeilen, ' + count('spare') + ' Ersatzteilzeilen, ' +
      count('minifig') + ' Minifigurenteilezeilen. Davon ausgeblendet: ' + hidden +
      '. Die Mengen werden erst mit „Speichern“ übernommen.';
    bulk.showModal();
  }
  byId('mark-all-existing').addEventListener('click', () => previewBulk(true));
  byId('reset-all-to-zero').addEventListener('click', () => previewBulk(false));
  byId('cancel-bulk').addEventListener('click', () => bulk.close());
  byId('apply-bulk').addEventListener('click', () => {
    for (const input of quantities) {
      input.value = pendingBulkValue ? input.dataset.required : '0';
      fieldError(input);
    }
    bulk.close();
    updateQuantityVisuals();
    filterRows();
    indicateDraft();
  });

  back.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || (!pending && !fields.some(changed))) return;
    event.preventDefault();
    byId('leave-message').textContent = pending ? 'Ein Speichervorgang läuft.' : 'Es gibt ungespeicherte Änderungen.';
    leave.showModal();
  });
  byId('stay-on-detail').addEventListener('click', () => leave.close());
  byId('discard-and-back').addEventListener('click', () => {
    if (pending) return;
    for (const field of fields) {
      field.value = field.dataset.saved;
      fieldError(field);
    }
    updateQuantityVisuals();
    uncertain.clear();
    indicateDraft();
    filterRows();
    leave.close();
    leaving = true;
    location.assign(back.href);
  });
  window.addEventListener('pageshow', event => {
    if (event.persisted && leaving) {
      // An explicitly discarded draft may have had an unconfirmed server write.
      // Reopen the same copy from the server when revisiting this history entry.
      leaving = false;
      location.replace(form.action);
    }
  });
  byId('save-and-back').addEventListener('click', async () => {
    leave.close();
    if (await save() && !fields.some(changed)) {
      leaving = true;
      location.assign(back.href);
    }
  });
  if (state.dataset.state === 'error') indicate('error', state.textContent);
  else if (fields.some(changed)) indicateDraft();
  updateQuantityVisuals();
  byId('set-title').focus({ preventScroll: true });
})();
