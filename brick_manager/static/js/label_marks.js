/* Explicit warehouse reprints; download never confirms physical printing. */
document.addEventListener('DOMContentLoaded', () => {
    const status = document.getElementById('marked-label-status');
    const list = document.getElementById('marked-label-list');
    const download = document.getElementById('marked-label-download');
    const confirm = document.getElementById('marked-label-confirm');
    const refresh = document.getElementById('marked-label-refresh');
    const token = document.querySelector('meta[name="warehouse-csrf"]').content;
    let marks = []; let downloaded = [];
    async function api(path, payload) {
        const response = await fetch(`/warehouse/label-marks${path}`, payload === undefined ? {} : {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': token }, body: JSON.stringify(payload)
        });
        if (!response.ok) { const error = await response.json(); throw new Error(error.error || 'Druckanfrage fehlgeschlagen.'); }
        return response;
    }
    async function load() {
        downloaded = []; confirm.disabled = true;
        marks = (await (await api('')).json()).marks;
        list.replaceChildren();
        for (const mark of marks) {
            const item = document.createElement('li'); item.textContent = mark.label + (mark.error ? ` · ${mark.error}` : ''); const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Vormerkung entfernen'; remove.className = 'btn btn-sm btn-outline-secondary ms-2';
            remove.addEventListener('click', async () => {
                remove.disabled = true;
                try { await api('/remove', { key: mark.key, generation: mark.generation }); await load(); }
                catch (error) { status.textContent = error.message; remove.disabled = false; }
            });
            item.append(remove); list.append(item);
        }
        status.textContent = `${marks.length} Boxen zum Neudruck vorgemerkt.`;
        download.disabled = !marks.length || marks.some(mark => mark.error);
    }
    refresh.addEventListener('click', () => load().catch(error => { status.textContent = error.message; }));
    download.addEventListener('click', async () => {
        download.disabled = true; confirm.disabled = true; downloaded = [];
        const selected = marks.map(mark => ({ key: mark.key, generation: mark.generation, fingerprint: mark.fingerprint }));
        try {
            const value = id => Number(document.getElementById(id)?.value || 0);
            const response = await api('/sheet', { marks: selected, start_position: value('label-start-position') || 1, horizontal_offset_mm: value('label-horizontal-offset'), vertical_offset_mm: value('label-vertical-offset') });
            const url = URL.createObjectURL(await response.blob()); const link = document.createElement('a'); link.href = url; link.download = 'marked_brick_labels.pdf'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
            downloaded = selected; confirm.disabled = false;
            status.textContent = 'PDF erstellt. Erst nach erfolgreichem Druck bestätigen; Vormerkungen bleiben bis dahin erhalten.';
        } catch (error) { status.textContent = error.message; }
        finally { download.disabled = !marks.length || marks.some(mark => mark.error); }
    });
    confirm.addEventListener('click', async () => {
        if (!downloaded.length || !window.confirm('Sind alle vorgemerkten Etiketten erfolgreich gedruckt?')) return;
        confirm.disabled = true;
        try { await api('/printed', { marks: downloaded }); await load(); }
        catch (error) { status.textContent = error.message; }
    });
    load().catch(error => { status.textContent = error.message; });
});
