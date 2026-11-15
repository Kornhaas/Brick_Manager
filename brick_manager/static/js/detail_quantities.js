/* Typed dashboard edits: one batch in flight; keep newer user intent queued. */
document.addEventListener('DOMContentLoaded', () => {
    const table = document.getElementById('detailsTable');
    if (!table) return;
    const feedback = document.getElementById('feedback');
    const status = document.getElementById('quantity-status');
    const retry = document.getElementById('quantity-retry');
    const pending = new Map();
    const invalid = new Set();
    let busy = false;
    const keyOf = change => `${change.part_type}:${change.part_id}`;
    function report(state, message) {
        feedback.classList.remove('d-none'); feedback.dataset.state = state;
        status.textContent = message; retry.hidden = state !== 'error' || !pending.size;
    }
    async function save() {
        if (busy || !pending.size) return;
        busy = true;
        try {
            while (pending.size) {
                const batch = [...pending.values()]; pending.clear();
                report('saving', 'Saving changes…');
                try {
                    const response = await fetch('/update_quantity', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({changes: batch.map(entry => entry.change)})
                    });
                    const payload = await response.json();
                    if (!response.ok) throw new Error(payload.error || 'Save failed.');
                    if (!Array.isArray(payload.updates)) throw new Error('Save acknowledgement is missing.');
                    const updates = new Map(payload.updates.map(update => [keyOf(update), update]));
                    if (batch.some(entry => !Number.isSafeInteger(updates.get(keyOf(entry.change))?.have_quantity))) throw new Error('Save acknowledgement is incomplete.');
                    for (const {input, change} of batch) {
                        const value = updates.get(keyOf(change)).have_quantity;
                        input.dataset.original = String(value);
                        if (!pending.has(keyOf(change)) && !invalid.has(keyOf(change)) && Number(input.value) === change.new_quantity) input.value = String(value);
                    }
                } catch (_) {
                    for (const entry of batch) {
                        const key = keyOf(entry.change);
                        if (!pending.has(key) && !invalid.has(key)) pending.set(key, entry);
                    }
                    report('error', 'Save failed. Your entries are still here. Please retry.');
                    return;
                }
            }
            report(invalid.size ? 'invalid' : 'saved', invalid.size ? 'Not saved: enter a whole number greater than or equal to 0.' : 'Changes saved successfully.');
        } finally { busy = false; }
    }
    document.addEventListener('input', event => {
        const input = event.target;
        if (!input?.matches?.('.update-quantity') || !table.contains(input)) return;
        const change = {part_id: Number(input.dataset.id), part_type: input.dataset.partType, new_quantity: Number(input.value)};
        const key = keyOf(change);
        if (!input.value.trim() || !Number.isSafeInteger(change.new_quantity) || change.new_quantity < 0) {
            invalid.add(key); pending.delete(key); input.setAttribute('aria-invalid', 'true');
            report('invalid', 'Not saved: enter a whole number greater than or equal to 0.');
            return;
        }
        invalid.delete(key); input.setAttribute('aria-invalid', 'false');
        if (!busy && change.new_quantity === Number(input.dataset.original)) return;
        pending.set(key, {input, change}); save();
    });
    retry.addEventListener('click', save);
});
