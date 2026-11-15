/* Physical warehouse UI. All user/catalog content is rendered as text. */
(function () {
    'use strict';

    const fillLabels = { unknown: 'Füllstand unbekannt', space: 'Platz vorhanden', nearly_full: 'Fast voll', full: 'Voll' };
    const relationLabels = { on_shelf: 'Auf Fachboden', stacked: 'Gestapelt', loose_on: 'Lose Auflage' };
    const state = { locations: [], types: [], units: [], placements: [], contents: [], stack_rules: [], moves: [], settings: {}, selectedUnit: null, selectedLegacyKey: null, legacy_groups: [] };
    const byId = id => document.getElementById(id);
    const getUnit = id => state.units.find(item => item.id === Number(id));
    const getLocation = id => state.locations.find(item => item.id === Number(id));
    const getPlacement = id => state.placements.find(item => item.unit_id === Number(id));
    const getType = id => state.types.find(item => item.id === Number(id));
    const token = document.querySelector('meta[name="warehouse-csrf"]').content;

    function element(tag, text, cls) {
        const node = document.createElement(tag);
        if (text !== undefined && text !== null) node.textContent = String(text);
        if (cls) node.className = cls;
        return node;
    }
    function empty(node) { node.replaceChildren(); }
    function status(message) { byId('warehouse-status').textContent = message; }
    function error(message) {
        byId('warehouse-error').hidden = !message;
        byId('warehouse-error').textContent = message || '';
    }
    async function api(path, method = 'GET', data) {
        const options = { method, headers: { Accept: 'application/json', 'X-CSRF-Token': token } };
        if (data !== undefined) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }
        const response = await fetch(`/warehouse${path}`, options);
        let payload;
        try { payload = await response.json(); } catch (_) { throw new Error('Antwort konnte nicht gelesen werden. Bitte erneut laden.'); }
        if (!response.ok) throw new Error(payload.error || 'Lageranfrage fehlgeschlagen.');
        return payload;
    }
    function unitLabel(unit) {
        const type = getType(unit.type_id);
        return `${unit.label || 'Ohne Etikett'} · ${type ? type.name : unit.kind} · #${unit.id}`;
    }
    function locationLabel(location) {
        const parts = []; const seen = new Set(); let item = location;
        while (item && !seen.has(item.id)) {
            seen.add(item.id); parts.unshift(item.kind === 'rack' ? `Regal ${item.label}` : item.kind === 'shelf' ? `Fach ${item.label}` : item.label); item = getLocation(item.parent_id);
        }
        return parts.join(' / ');
    }
    function address(unit) {
        if (!unit) return 'Fundort ungeklärt';
        const parts = []; const seen = new Set(); let item = unit;
        while (item && !seen.has(item.id)) {
            seen.add(item.id); parts.unshift(unitLabel(item));
            if (item.host_unit_id) { item = getUnit(item.host_unit_id); continue; }
            const placement = getPlacement(item.id);
            if (!placement) return `Fundort ungeklärt / ${parts.join(' / ')}`;
            if (placement.support_unit_id) { item = getUnit(placement.support_unit_id); continue; }
            const location = getLocation(placement.shelf_id);
            return `${location ? locationLabel(location) : 'Fach ungeklärt'} / ${parts.join(' / ')}`;
        }
        return `Aufstellung ungeklärt / ${parts.join(' / ')}`;
    }
    function contentLabel(content) {
        return `${content.part_num} · Farbe ${content.color_id ?? 'unbekannt'} · ${content.quantity ?? 'ungezählt'} · ${content.storage_unit_id ? unitLabel(getUnit(content.storage_unit_id) || { id: content.storage_unit_id }) : 'Fundort ungeklärt'} · #${content.id}`;
    }
    function rowsForOptions(kind) {
        const active = state.units.filter(unit => unit.active !== false);
        switch (kind) {
            case 'locations': return state.locations.map(item => [item.id, locationLabel(item)]).sort((a, b) => natural(a[1], b[1]));
            case 'shelves': return state.locations.filter(item => item.kind === 'shelf').map(item => [item.id, locationLabel(item)]).sort((a, b) => natural(a[1], b[1]));
            case 'types': return state.types.map(item => [item.id, item.name]);
            case 'units': return active.map(item => [item.id, unitLabel(item)]);
            case 'outer-units': return active.filter(item => !item.host_unit_id).map(item => [item.id, unitLabel(item)]);
            case 'unplaced-units': return active.filter(item => !item.host_unit_id && !getPlacement(item.id)).map(item => [item.id, unitLabel(item)]);
            case 'drawers': return active.filter(item => item.kind === 'drawer').map(item => [item.id, address(item)]);
            case 'content-units': return active.filter(item => ['container', 'compartment'].includes(item.kind) || (item.kind === 'drawer' && item.partition_count === 1)).map(item => [item.id, address(item)]);
            case 'contents': return (state.allContents || state.contents).map(item => [item.id, contentLabel(item)]);
            case 'planned-sets': return (state.settings.planned_sets || []).map(item => [item.id, `${item.set_num} × ${item.quantity} ${item.active ? 'aktiv' : 'inaktiv'}`]);
            default: return [];
        }
    }
    function fillSelect(select, rows, emptyLabel) {
        const selected = select.value;
        empty(select);
        if (emptyLabel !== undefined) select.add(new Option(emptyLabel, ''));
        rows.forEach(([id, text]) => select.add(new Option(text, String(id))));
        if ([...select.options].some(option => option.value === selected)) select.value = selected;
    }
    const lastShelfKey = 'brick-manager.warehouse.last-shelf';
    let shelfSelectionInitialized = false;
    function rememberShelf() {
        const value = byId('warehouse-shelf').value;
        if (value) {
            try { localStorage.setItem(lastShelfKey, value); } catch (_) { /* Browser storage may be disabled. */ }
        }
    }
    function refreshOptions() {
        const shelf = byId('warehouse-shelf');
        const previous = shelf.value;
        document.querySelectorAll('[data-options]').forEach(select => fillSelect(select, rowsForOptions(select.dataset.options), select.dataset.empty));
        const shelves = rowsForOptions('shelves');
        fillSelect(shelf, shelves, shelves.length ? 'Alle Fächer' : 'Noch kein Fach erfasst');
        shelf.disabled = !shelves.length;
        if (!shelfSelectionInitialized || previous && ![...shelf.options].some(option => option.value === previous)) {
            let saved;
            try { saved = localStorage.getItem(lastShelfKey); } catch (_) { /* Use the first shelf without browser storage. */ }
            shelf.value = [...shelf.options].some(option => option.value && option.value === saved) ? saved : shelf.options[1]?.value || '';
            shelfSelectionInitialized = shelf.options.length > 1;
            rememberShelf();
        }
    }
    function withPrintMark(button, target, enabled = true) {
        const wrapper = element('div', null, 'warehouse-card-slot');
        const label = element('label', null, 'warehouse-print-mark');
        const checkbox = element('input'); checkbox.type = 'checkbox';
        checkbox.checked = (state.labelMarks || []).some(mark => Object.keys(target).every(key => mark.target[key] === target[key]));
        checkbox.disabled = !enabled;
        label.append(checkbox, document.createTextNode(' Etikett neu drucken'));
        if (!enabled) label.title = 'Zuerst Schrank, Fach und Box zuordnen.';
        checkbox.addEventListener('change', async () => {
            const marked = checkbox.checked; checkbox.disabled = true;
            try {
                await api('/label-marks', 'POST', { ...(target.unit_id ? target : { storage_id: Number(wrapper.dataset.storageId) }), marked });
                state.labelMarks = (await api('/label-marks')).marks;
                status(`${state.labelMarks.length} Boxen zum Etikettendruck vorgemerkt. Auf der Etikettendruckseite gesammelt drucken.`);
            } catch (problem) { checkbox.checked = !marked; error(problem.message); }
            finally { checkbox.disabled = false; }
        });
        wrapper.append(button, label); return wrapper;
    }
    function unitButton(unit, placement) {
        const button = element('button', null, 'warehouse-unit'); button.type = 'button';
        button.dataset.unitId = unit.id;
        if (placement) button.dataset.relation = placement.relation_kind;
        const type = getType(unit.type_id);
        if (type && type.width_mm) button.style.inlineSize = `${Math.max(150, Math.min(type.width_mm * 0.85, 330))}px`;
        if (type && type.height_mm) button.style.minBlockSize = `${Math.max(75, Math.min(type.height_mm * 0.7, 150))}px`;
        button.append(element('strong', unitLabel(unit)));
        button.append(element('small', fillLabels[unit.fill_state] || fillLabels.unknown));
        if (placement) {
            button.append(element('small', relationLabels[placement.relation_kind]));
            if (placement.support_unit_id) {
                const support = getUnit(placement.support_unit_id);
                const verified = support && state.stack_rules.some(rule => rule.lower_type_id === support.type_id && rule.upper_type_id === unit.type_id && rule.relation_kind === placement.relation_kind && rule.verified);
                if (!verified) button.append(element('small', 'Kombination noch nicht verifiziert'));
            }
        }
        button.setAttribute('aria-current', String(state.selectedUnit === unit.id));
        button.addEventListener('click', () => selectUnit(unit.id));
        return withPrintMark(button, { unit_id: unit.id });
    }
    function addStack(container, unit, visited) {
        if (visited.has(unit.id)) { container.append(element('p', 'Aufstellung prüfen: zyklische Beziehung.')); return; }
        visited.add(unit.id);
        container.append(unitButton(unit, getPlacement(unit.id)));
        const supported = state.placements.filter(item => item.support_unit_id === unit.id).sort((a, b) => a.order_left - b.order_left);
        if (supported.length) {
            const branches = element('div', null, 'warehouse-branches');
            for (const placement of supported) {
                const child = getUnit(placement.unit_id); if (!child) continue;
                const stack = element('div', null, 'warehouse-stack');
                addStack(stack, child, new Set(visited)); branches.append(stack);
            }
            container.append(branches);
        }
    }
    const natural = (a, b) => String(a ?? '').localeCompare(String(b ?? ''), 'de', { numeric: true });
    function legacyAddress(group) {
        return `Regal ${group.location || 'unbekannt'} / Fach ${group.level || 'unbekannt'} / Box ${group.box || 'ohne Beschriftung'}`;
    }
    function partIcon(item) {
        const icon = element('span', null, 'warehouse-part-image');
        const fallback = element('span', '▧', 'warehouse-part-icon'); fallback.setAttribute('aria-hidden', 'true');
        icon.append(fallback);
        if (item.part_img_url) {
            try {
                const url = new URL(item.part_img_url, location.origin);
                if (['http:', 'https:'].includes(url.protocol)) {
                    const image = element('img'); image.src = url.href; image.alt = ''; image.loading = 'lazy'; image.referrerPolicy = 'no-referrer';
                    image.addEventListener('load', () => { fallback.hidden = true; });
                    image.addEventListener('error', () => { image.remove(); fallback.hidden = false; });
                    icon.append(image);
                }
            } catch (_) { /* Keep the fallback for invalid catalog URLs. */ }
        }
        return icon;
    }
    function legacyButton(group) {
        const button = element('button', null, 'warehouse-legacy-card'); button.type = 'button';
        button.dataset.legacyKey = group.key;
        button.append(element('strong', group.box ? `Box ${group.box}` : 'Box ohne Beschriftung'));
        if (!group.shelf_id) button.append(element('small', legacyAddress(group)));
        const previews = element('span', null, 'warehouse-part-previews');
        const variants = [...new Map((group.contents || []).map(item => [`${item.part_num}:${item.color_id}`, item])).values()];
        for (const item of variants.slice(0, 3)) {
            const preview = element('span', null, 'warehouse-part-preview');
            preview.append(partIcon(item));
            const text = element('span');
            text.append(element('span', item.part_name || 'Katalogdaten fehlen'), element('small', `Teil ${item.part_num} · Farbe ${item.color_name || (item.color_id ?? 'unbekannt')}`));
            preview.append(text); previews.append(preview);
        }
        if (variants.length > 3) previews.append(element('small', `+ ${variants.length - 3} weitere Varianten`));
        button.append(previews);
        button.append(element('small', `${group.row_count} Inhaltszuordnungen · ${group.variant_count} Varianten`));
        button.append(element('small', 'Beschriftungsgruppe · Behälter noch bestätigen'));
        button.setAttribute('aria-current', String(state.selectedLegacyKey === group.key));
        button.addEventListener('click', () => selectLegacyGroup(group.key));
        const target = { location: group.location, level: group.level, box: group.box };
        const wrapper = withPrintMark(button, target, [group.location, group.level, group.box].every(value => typeof value === 'string' && value.trim()));
        // The server resolves the raw group from its existing content ID.
        wrapper.dataset.storageId = group.storage_ids[0];
        return wrapper;
    }
    function legacyCards(parent, groups) {
        const cards = element('div', null, 'warehouse-legacy-grid');
        const searchLabel = element('label', 'Beschriftung suchen ');
        const search = element('input'); search.type = 'search'; search.placeholder = 'Regal, Fach oder Box'; searchLabel.append(search);
        const more = element('button', 'Weitere Beschriftungsgruppen anzeigen'); more.type = 'button';
        let limit = 24;
        function draw() {
            empty(cards);
            const query = search.value.toLocaleLowerCase('de');
            const filtered = groups.filter(group => legacyAddress(group).toLocaleLowerCase('de').includes(query)).sort((a, b) => natural(a.box, b.box) || natural(legacyAddress(a), legacyAddress(b)));
            const rows = Number(byId('warehouse-column-rows').value) || 3;
            cards.style.gridTemplateRows = `repeat(${rows}, auto)`;
            filtered.slice(0, limit).forEach((group, index) => {
                const card = legacyButton(group);
                card.style.gridRow = String(rows - index % rows);
                card.style.gridColumn = String(Math.floor(index / rows) + 1);
                cards.append(card);
            });
            more.hidden = filtered.length <= limit;
        }
        search.addEventListener('input', () => { limit = 24; draw(); });
        more.addEventListener('click', () => { limit += 24; draw(); });
        if (groups.length > 24) parent.append(searchLabel);
        parent.append(cards, more); draw();
    }
    function editLegacyContent(item) {
        const form = byId('warehouse-content-form');
        for (const name of ['part_num', 'color_id', 'quantity', 'notes']) form.elements[name].value = item[name] ?? '';
        form.elements.id.value = item.id; form.elements.storage_unit_id.value = '';
        byId('warehouse-capture').open = true;
        form.scrollIntoView({ block: 'center' }); form.elements.storage_unit_id.focus();
        status(`Bestehende Inhaltszuordnung #${item.id} ausgewählt. Erst nach physischer Prüfung einen Behälter wählen und speichern.`);
    }
    async function selectLegacyGroup(key, focus = true) {
        const group = state.legacy_groups.find(item => item.key === key); if (!group) return;
        state.selectedLegacyKey = key; state.selectedUnit = null;
        if (!group.contents) {
            byId('warehouse-details').replaceChildren(element('p', 'Inhalte werden geladen …'));
            try {
                Object.assign(group, await api(`/contents/${group.storage_ids[0]}/group`));
                if (state.selectedLegacyKey !== key) return;
                const known = new Set(state.contents.map(item => item.id));
                state.contents.push(...group.contents.filter(item => !known.has(item.id)));
                refreshOptions();
            } catch (problem) { error(problem.message); return; }
        }
        const container = byId('warehouse-details'); empty(container);
        container.append(element('h3', legacyAddress(group)));
        container.append(element('p', 'Beschriftungsgruppe aus bestehenden Zuordnungen. Noch nicht als physischer Behälter bestätigt; Anzahl, Stapel und Stellfläche sind ungeprüft.', 'warehouse-note'));
        if (!group.shelf_id) container.append(element('p', 'Das Fach ist nicht eindeutig zugeordnet. Die bisherigen Beschriftungen bleiben unverändert erhalten.'));
        const tableHost = element('div'); container.append(tableHost);
        const more = element('button', 'Weitere Inhaltszuordnungen anzeigen'); more.type = 'button';
        let limit = 50;
        function draw() {
            empty(tableHost);
            renderTable(tableHost, ['Bild', 'Teil', 'Farbe', 'Menge', 'Notiz', 'Zuordnung'], group.contents.slice(0, limit).map(item => {
                const button = element('button', `#${item.id} Behälter zuordnen`); button.type = 'button';
                button.addEventListener('click', () => editLegacyContent(item));
                return [partIcon(item), item.part_name ? `${item.part_num} · ${item.part_name}` : item.part_num, item.color_name || (item.color_id ?? 'unbekannt'), item.quantity ?? 'ungezählt', item.notes || '–', button];
            }));
            more.hidden = group.contents.length <= limit;
        }
        more.addEventListener('click', () => { limit += 50; draw(); }); container.append(more); draw();
        renderLayout(); if (focus) byId('detail-title').focus();
    }
    function renderLayout() {
        const layout = byId('warehouse-layout'); empty(layout);
        const selected = Number(byId('warehouse-shelf').value) || null;
        const shelves = state.locations.filter(item => item.kind === 'shelf' && (!selected || selected === item.id)).sort((a, b) => natural(locationLabel(a), locationLabel(b)));
        if (!shelves.length) layout.append(element('p', 'Noch kein Fach erfasst. Lege unter „Lagerstruktur“ eine Zone, ein Regal und ein Fach an.'));
        for (const shelf of shelves) {
            const section = element('section', null, 'warehouse-shelf');
            section.append(element('h3', locationLabel(shelf)));
            const stacks = element('div', null, 'warehouse-stacks');
            const roots = state.placements.filter(item => item.shelf_id === shelf.id).sort((a, b) => a.order_left - b.order_left);
            const legacy = state.legacy_groups.filter(group => group.shelf_id === shelf.id);
            if (!roots.length && !legacy.length) stacks.append(element('p', 'Keine Inhaltszuordnungen oder bestätigten Einheiten in diesem Fach.'));
            for (const placement of roots) {
                const unit = getUnit(placement.unit_id); if (!unit) continue;
                const stack = element('div', null, 'warehouse-stack');
                addStack(stack, unit, new Set()); stacks.append(stack);
            }
            section.append(stacks);
            if (legacy.length) {
                section.append(element('p', 'Vorhandene Beschriftungen · Aufstellung und Behälter noch vor Ort bestätigen. Keine maßstäbliche Platzdarstellung.'));
                legacyCards(section, legacy);
            }
            layout.append(section);
        }
        const unplaced = state.units.filter(unit => !unit.host_unit_id && unit.active !== false && !getPlacement(unit.id));
        if (unplaced.length) {
            const section = element('section'); section.append(element('h3', 'Einheiten mit ungeklärter Aufstellung'));
            unplaced.forEach(unit => section.append(unitButton(unit))); layout.append(section);
        }
        const unlocated = state.legacy_groups.filter(group => !group.shelf_id);
        if (unlocated.length) {
            const section = element('details', null, 'warehouse-unlocated');
            section.append(element('summary', `Fundort noch zuordnen · ${unlocated.length} Beschriftungsgruppen`));
            section.append(element('p', 'Fehlende oder mehrdeutige Beschriftungen werden keinem Fach zugeschrieben. Suche über die erhaltenen Angaben und öffne die Inhalte.'));
            legacyCards(section, unlocated); layout.append(section);
        }
        const box = byId('warehouse-unresolved'); empty(box);
        box.append(element('p', `${state.legacy_groups.length} bestehende Beschriftungsgruppen sind oben in der Lagerübersicht sichtbar. Öffne dort eine Gruppe und wähle eine Inhaltszuordnung zur physischen Bestätigung.`));
    }

    function appendList(parent, title, values) {
        if (!values || !values.length) return;
        parent.append(element('h4', title)); const list = element('ul');
        values.forEach(value => list.append(element('li', typeof value === 'object' ? JSON.stringify(value) : value))); parent.append(list);
    }
    function renderTable(parent, headings, rows) {
        const table = element('table'); const head = element('thead'); const header = element('tr');
        headings.forEach(text => { const cell = element('th', text); cell.scope = 'col'; header.append(cell); });
        head.append(header); table.append(head); const body = element('tbody');
        rows.forEach(values => { const row = element('tr'); values.forEach(value => { const cell = element('td'); cell.append(value instanceof Node ? value : document.createTextNode(String(value ?? 'unbekannt'))); row.append(cell); }); body.append(row); });
        table.append(body); parent.append(table);
    }
    async function selectUnit(id) {
        try {
            error(''); const details = await api(`/units/${id}`); state.selectedLegacyKey = null; state.selectedUnit = Number(id);
            const unit = details.unit || details; const known = getUnit(id) || unit;
            const container = byId('warehouse-details'); empty(container);
            container.append(element('h3', unitLabel(known)));
            container.append(element('p', `Aktuell: ${address(known)}`));
            container.append(element('p', `${fillLabels[known.fill_state] || fillLabels.unknown} · Inhalt ${known.contents_complete ? 'vollständig erfasst' : 'noch nicht vollständig erfasst'}`));
            const placement = getPlacement(known.id);
            if (placement) container.append(element('p', relationLabels[placement.relation_kind]));
            const type = getType(known.type_id);
            if (type) container.append(element('p', `Zugriff: ${type.access_mode === 'front_open' ? 'Von vorne offen; Entnahme der ganzen Box kann Abnehmen oberer Einheiten erfordern.' : type.access_mode === 'remove_above' ? 'Obere Behälter für Deckelzugriff abnehmen.' : type.access_mode === 'drawer' ? 'Schublade nach vorne ausziehen; Freiraum prüfen.' : 'Zugriff noch vor Ort prüfen.'}`));
            const supported = state.placements.filter(item => item.support_unit_id === known.id);
            if (supported.length) container.append(element('p', `Auf dieser Einheit stehen: ${supported.map(item => unitLabel(getUnit(item.unit_id))).join(', ')}. Vor Entnahme abnehmen oder ausdrücklich mitplanen.`));
            const children = state.units.filter(item => item.host_unit_id === known.id && item.active !== false);
            if (children.length) {
                container.append(element('h4', known.kind === 'cabinet' ? 'Schubladen' : 'Unterteilungen'));
                children.sort((a, b) => a.ordinal - b.ordinal).forEach(child => container.append(unitButton(child)));
            }
            const contents = state.contents.filter(item => item.storage_unit_id === known.id);
            if (contents.length) renderTable(container, ['Bild', 'Teil', 'Farbe', 'Gezählte Menge', 'Zuordnung'], contents.map(item => [partIcon(item), item.part_name ? `${item.part_num} · ${item.part_name}` : item.part_num, item.color_name || (item.color_id ?? 'unbekannt'), item.quantity === null ? 'ungezählt' : item.quantity, `#${item.id}`]));
            else container.append(element('p', known.contents_complete ? 'Kein Inhalt erfasst. Eine leere Einheit belegt weiterhin ihre Stellfläche.' : 'Kein Inhalt erfasst; das beweist noch nicht, dass die Einheit leer ist.'));
            appendList(container, 'Zugriff / Hinweise', details.warnings || details.blockers || []);
            const labelLink = element('a', 'Etikett für diese Einheit herunterladen'); labelLink.href = `/warehouse/units/${id}/label`; container.append(labelLink);
            const printed = element('button', 'Erfolgreichen Etikettdruck bestätigen'); printed.type = 'button';
            printed.addEventListener('click', () => act(printed, async () => { await api(`/units/${id}/printed`, 'POST', { revision: known.revision }); await load(); status('Etikettdruck bestätigt.'); })); container.append(printed);
            const moveForm = byId('warehouse-move-form'); moveForm.elements.unit_id.value = String(id);
            const checkForm = byId('warehouse-unit-update-form'); checkForm.elements.id.value = String(id); checkForm.elements.fill_state.value = known.fill_state || 'unknown'; checkForm.elements.contents_complete.checked = !!known.contents_complete;
            const params = new URLSearchParams(location.search); params.set('unit_id', id); history.replaceState(null, '', `${location.pathname}?${params}`);
            renderLayout(); byId('detail-title').focus();
        } catch (problem) { error(problem.message); }
    }
    function moveDescription(move) {
        const payload = move.payload || {}; const names = { unit: 'Behälter verschieben', quantity: 'Teilmenge umbuchen', intake: 'Bricks aufnehmen', count: 'Bestandszählung' };
        const statusNames = { draft: 'Entwurf', planned: 'Geplant – noch nicht physisch bestätigt', confirmed: 'Physisch bestätigt', cancelled: 'Abgebrochen' };
        return `#${move.id}: ${names[move.kind] || move.kind} · ${statusNames[move.status] || move.status}${move.reason ? ` · ${move.reason}` : ''}${payload.quantity ? ` · Menge ${payload.quantity}` : ''}`;
    }
    function renderMoves() {
        const parent = byId('warehouse-moves'); empty(parent);
        if (!state.moves.length) { parent.append(element('p', 'Noch keine Umräumaufträge.')); return; }
        for (const move of state.moves) {
            const row = element('article', null, 'warehouse-move'); row.append(element('h3', moveDescription(move)));
            const payload = move.payload || {};
            for (const item of payload.items || [payload]) {
                if (item.unit_id) row.append(element('p', `Einheit: ${getUnit(item.unit_id) ? unitLabel(getUnit(item.unit_id)) : item.unit_id}`));
                if (item.storage_id) {
                    const source = state.contents.find(content => content.id === item.storage_id);
                    row.append(element('p', `Quelle: ${source ? contentLabel(source) : `Inhaltszeile #${item.storage_id}`} · Umbuchungsmenge ${item.quantity}`));
                }
                if (item.target_unit_id) row.append(element('p', `Ziel: ${getUnit(item.target_unit_id) ? address(getUnit(item.target_unit_id)) : item.target_unit_id} · Menge ${item.quantity}`));
                if (item.target_placement) {
                    const target = item.target_placement;
                    row.append(element('p', target.remove ? 'Geplantes Ziel: Leere Einheit aus Aufstellung nehmen.' : `Geplantes Ziel: ${target.support_unit_id ? `auf ${getUnit(target.support_unit_id) ? unitLabel(getUnit(target.support_unit_id)) : target.support_unit_id}` : getLocation(target.shelf_id) ? locationLabel(getLocation(target.shelf_id)) : 'ungeklärt'} · ${relationLabels[target.relation_kind] || ''}`));
                }
            }
            for (const effect of move.preview || []) {
                row.append(element('p', `Geplante Auswirkung: ${effect.container_emptied ? 'Behälter wird leer. ' : ''}${effect.stack_lowered ? 'Stapel wird niedriger. ' : ''}${effect.base_area_released ? 'Basisfläche kann frei werden. ' : 'Keine Basisfläche allein durch Entleeren frei. '}${effect.measurement_note || ''}`));
            }
            for (const fit of (move.snapshot || {}).previews || []) {
                row.append(element('p', fit.status === 'no_fit' ? 'Ziel passt nicht.' : fit.status === 'fits' || fit.status === 'fit' ? 'Gemessene Passung geprüft.' : 'Passung vor Ort prüfen.'));
                appendList(row, 'Passprüfung', fit.reasons || []);
            }
            const before = (move.snapshot || {}).space_before || {};
            const after = (move.snapshot || {}).space_after || {};
            for (const shelfId of Object.keys(before)) {
                const location = getLocation(shelfId);
                const old = before[shelfId]; const current = after[shelfId];
                if (!current) continue;
                row.append(element('p', `${location ? locationLabel(location) : `Fach #${shelfId}`}: belegte Basispositionen ${old.base_count} → ${current.base_count}.`));
                if (old.fit_known && current.fit_known) row.append(element('p', `Freie zusammenhängende Intervalle in mm vorher ${JSON.stringify(old.free_intervals_mm)}, nachher ${JSON.stringify(current.free_intervals_mm)}.`));
                else row.append(element('p', 'Zusammenhängende freie Fläche bleibt ohne vollständige Messwerte ungeprüft.'));
            }
            appendList(row, 'Prüfhinweise', (move.snapshot || {}).warnings || []);
            if (['draft', 'planned'].includes(move.status)) {
                const action = element('button', move.status === 'draft' ? 'Plan übernehmen und reservieren' : 'Physisch umgeräumt – bestätigen'); action.type = 'button';
                action.addEventListener('click', async () => {
                    if (move.status === 'planned' && !window.confirm('Ist die Bewegung physisch ausgeführt? Aufnahmefähigkeit, Passung und sichere Auflage vor Ort geprüft? Der Ist-Fundort und die Mengen werden jetzt geändert.')) return;
                    await act(action, async () => {
                        const endpoint = move.status === 'draft' ? 'plan' : 'confirm';
                        await api(`/moves/${move.id}/${endpoint}`, 'POST', { revision: move.revision, idempotency_key: move.idempotency_key, capacity_confirmed: true, physical_fit_confirmed: true });
                        await load(); status(endpoint === 'plan' ? 'Plan reserviert. Der aktuelle Fundort bleibt unverändert.' : 'Physische Bewegung bestätigt.');
                    });
                }); row.append(action);
                const cancel = element('button', 'Plan abbrechen'); cancel.type = 'button';
                cancel.addEventListener('click', () => act(cancel, async () => { await api(`/moves/${move.id}/cancel`, 'POST', {}); await load(); status('Plan abgebrochen.'); })); row.append(cancel);
            }
            parent.append(row);
        }
    }
    async function act(button, callback) {
        button.disabled = true; error('');
        try { await callback(); } catch (problem) { error(problem.message); } finally { button.disabled = false; }
    }
    function values(form) {
        const data = {};
        for (const input of form.elements) {
            if (!input.name) continue;
            if (input.type === 'checkbox') data[input.name] = input.checked;
            else if (input.type === 'number' || input.tagName === 'SELECT' && (input.dataset.options || input.name === 'partition_count')) data[input.name] = input.value === '' ? null : Number(input.value);
            else data[input.name] = input.value.trim();
        }
        return data;
    }
    function bindForm(id, callback) {
        const form = byId(id);
        form.addEventListener('submit', event => {
            event.preventDefault(); const button = form.querySelector('button');
            act(button, async () => { await callback(values(form), form); await load(); status('Gespeichert.'); });
        });
    }
    async function loadSpace() {
        const id = byId('warehouse-shelf').value; const box = byId('warehouse-space'); empty(box);
        if (!id) return;
        try {
            const report = await api(`/locations/${id}`);
            box.append(element('h3', 'Stellfläche und Messstatus'));
            const legacy = state.legacy_groups.some(group => group.shelf_id === Number(id));
            if (legacy || report.legacy_occupancy_unknown) box.append(element('p', 'Vorhandene Inhaltszuordnungen belegen dieses Fach; Behälter und Anordnung sind noch ungeprüft. Freie Stellfläche ist deshalb noch nicht bestimmbar.', 'warehouse-note'));
            else if (report.fit_known && report.free_intervals_mm?.length) box.append(element('p', `Freie zusammenhängende Intervalle (mm): ${report.free_intervals_mm.map(interval => interval.join('–')).join(', ')}`));
            if (report.note) box.append(element('p', report.note));
            box.append(element('p', report.fit_known ? 'Geometrie gemessen; konkrete neue Aufstellung separat prüfen.' : 'Passung ungeprüft: erforderliche Maße oder Positionen fehlen.'));
            if (report.empty_units) box.append(element('p', `Leere Behälter: ${report.empty_units.length ?? report.empty_units}; sie belegen weiterhin Platz.`));
            appendList(box, 'Hinweise zur Passung', report.reasons || report.warnings || report.missing || []);
            if (report.status) box.append(element('p', `Mess-/Planungsstatus: ${report.status}`));
        } catch (problem) { error(problem.message); }
    }
    let loadGeneration = 0;
    async function load() {
        const generation = ++loadGeneration;
        byId('warehouse-archive').disabled = true;
        try {
            const params = new URLSearchParams({ view: 'focused' });
            let shelf = byId('warehouse-shelf').value;
            if (!shelfSelectionInitialized) {
                try { shelf = localStorage.getItem(lastShelfKey) || ''; } catch (_) { /* First shelf on server. */ }
            } else if (!shelf) params.set('all', '1');
            if (shelf) params.set('shelf_id', shelf);
            const [snapshot, moves, settings, marks] = await Promise.all([api(`/data?${params}`), api('/moves'), api('/settings'), api('/label-marks')]);
            if (generation !== loadGeneration) return;
            state.allContents = null;
            state.labelMarks = marks.marks || [];
            for (const key of ['locations', 'types', 'units', 'placements', 'contents', 'stack_rules', 'legacy_groups']) state[key] = snapshot[key] || [];
            state.moves = moves.items || []; state.settings = settings;
            refreshOptions();
            if (snapshot.selected_shelf_id !== null && snapshot.selected_shelf_id !== undefined) {
                byId('warehouse-shelf').value = String(snapshot.selected_shelf_id); rememberShelf();
            }
            renderLayout(); renderMoves();
            const summary = byId('warehouse-settings-summary'); empty(summary);
            appendList(summary, 'Kategoriezuordnungen', (settings.category_rules || []).map(rule => `Kategorie #${rule.category_id} → ${getLocation(rule.location_id) ? locationLabel(getLocation(rule.location_id)) : `Ort #${rule.location_id}`}${rule.archive_location_id ? ` · Archiv: ${getLocation(rule.archive_location_id) ? locationLabel(getLocation(rule.archive_location_id)) : rule.archive_location_id}` : ''}`));
            appendList(summary, 'Geplante Sets', (settings.planned_sets || []).map(plan => `${plan.set_num} × ${plan.quantity} · ${plan.active ? 'aktiv geplant' : 'inaktiv'}`));
            appendList(summary, 'Manuelle Hinweise', (settings.preferences || []).map(preference => `${preference.part_num} · Farbe ${preference.color_id ?? 'unbekannt'}${preference.keep_accessible ? ' · griffbereit halten' : ''}${preference.replenishment_unlikely ? ' · Nachschub unwahrscheinlich' : ''}`));
            const ruleForm = byId('warehouse-settings-form');
            for (const name of ['max_known_sets', 'min_age_years', 'catalog_max_age_days']) {
                if (settings[name] !== undefined) ruleForm.elements[name].value = settings[name];
            }
            ruleForm.elements.planning_reviewed.checked = !!settings.planning_reviewed;
            status(`${snapshot.legacy_summary?.content_rows ?? state.contents.length} Inhaltszuordnungen · ${snapshot.legacy_summary?.legacy_groups ?? state.legacy_groups.length} bestehende Beschriftungsgruppen · ${state.units.length} physisch erfasste Einheiten. Beschriftungen bleiben erhalten; Behälter und Maße vor Ort bestätigen.`);
            if (state.selectedLegacyKey) {
                if (state.legacy_groups.some(group => group.key === state.selectedLegacyKey)) selectLegacyGroup(state.selectedLegacyKey, false);
                else { state.selectedLegacyKey = null; byId('warehouse-details').textContent = 'Alle Inhaltszuordnungen dieser Beschriftungsgruppe sind jetzt einem Behälter zugeordnet.'; }
            }
            await loadSpace();
        } finally { if (generation === loadGeneration) byId('warehouse-archive').disabled = false; }
    }
    async function showSearch(data) {
        const query = data.color_id === null ? '' : `?color_id=${encodeURIComponent(data.color_id)}`;
        const [places, suggestion] = await Promise.all([api(`/parts/${encodeURIComponent(data.part_num)}/locations${query}`), api(`/parts/${encodeURIComponent(data.part_num)}/suggestion${query}`)]);
        const box = byId('warehouse-search-results'); empty(box);
        box.append(element('h3', `Bricks ${data.part_num}`));
        for (const place of places.items || []) {
            const row = element('p'); const unitId = place.storage_unit_id || place.unit_id;
            const link = element('a', unitId && getUnit(unitId) ? address(getUnit(unitId)) : `${place.location ?? '?'} / ${place.level ?? '?'} / ${place.box ?? '?'}`);
            if (unitId) { link.href = `/warehouse?unit_id=${encodeURIComponent(unitId)}`; link.addEventListener('click', event => { event.preventDefault(); selectUnit(unitId); }); }
            else {
                const group = state.legacy_groups.find(item => item.storage_ids.includes(place.id));
                link.href = '#detail-title';
                link.addEventListener('click', async event => {
                    event.preventDefault();
                    try {
                        const target = group || await api(`/contents/${place.id}/group`);
                        if (!group) state.legacy_groups.push(target);
                        await selectLegacyGroup(target.key);
                    } catch (problem) { error(problem.message); }
                });
            }
            row.append(link, document.createTextNode(` · Farbe ${place.color_id ?? 'unbekannt'} · Menge ${place.quantity ?? 'ungezählt'}`)); box.append(row);
            for (const move of place.planned_moves || []) box.append(element('p', `Geplant, noch nicht umgeräumt: ${move.destination}${move.quantity === null ? '' : ` · Menge ${move.quantity}`}`));
        }
        if (!(places.items || []).length) box.append(element('p', 'Noch kein bestätigter Fundort erfasst.'));
        if (suggestion.category_id !== undefined) box.append(element('p', `Kategorie #${suggestion.category_id}`));
        if (suggestion.default_location_id) {
            const target = getLocation(suggestion.default_location_id); box.append(element('p', `Standard: ${target ? locationLabel(target) : `Ort #${suggestion.default_location_id}`}`));
        }
        appendList(box, 'Begründung des Vorschlags', suggestion.reasons || []);
        appendList(box, 'Fehlende Angaben', suggestion.missing || []);
        const historyData = suggestion.history || {};
        if (historyData.known_set_count !== undefined) box.append(element('p', `${historyData.known_set_count} bekannte unterschiedliche Sets · erstes Jahr ${historyData.first_year ?? 'unbekannt'} · letztes Jahr ${historyData.last_year ?? 'unbekannt'}`));
        const form = byId('warehouse-move-form'); form.elements.kind.value = 'intake'; form.elements.part_num.value = data.part_num; form.elements.color_id.value = data.color_id ?? '';
        form.elements.target_unit_id.value = suggestion.target_unit_id ? String(suggestion.target_unit_id) : '';
        form.elements.quantity.value = '';
    }
    async function showArchive() {
        const shelf = byId('warehouse-shelf').value;
        if (!shelf) throw new Error('Bitte zuerst ein Fach auswählen.');
        const report = await api(`/locations/${shelf}/suggestions`); const box = byId('warehouse-archive-results'); empty(box);
        box.append(element('h3', 'Archivprüfung für dieses Fach'));
        box.append(element('p', 'Diese Liste verschiebt nichts. Prüfe Eigenbedarf, gesamten Inhalt und freien Zielplatz; erst danach einen Umräumauftrag erstellen.'));
        for (const item of report.units || []) {
            const article = element('article', null, 'warehouse-move');
            article.append(element('h4', `${item.label || `Einheit #${item.unit_id}`} · ${item.whole_box ? 'Ganze Box prüfen' : 'Teilumbuchung / Inhalte prüfen'}`));
            if (item.hint) article.append(element('p', item.hint, 'warehouse-note'));
            appendList(article, 'Begründung', item.reasons || []);
            const effects = item.effects || {};
            article.append(element('p', `Auswirkung: Leerer Behälter gibt keine Stellfläche frei. ${effects.lower_stack_if_removed ? 'Entfernen dieser Einheit kann den Stapel niedriger machen.' : ''} ${effects.base_area_if_removed ? 'Entfernen der Einheit kann ihre Basisfläche freigeben.' : 'Keine bestätigte freie Basisfläche allein durch Entleeren.'} Zusammenhängende Stellfläche und Passung gesondert prüfen.`));
            if ((item.archive_location_ids || []).length) article.append(element('p', `Archivziele zur Prüfung: ${item.archive_location_ids.map(id => getLocation(id) ? locationLabel(getLocation(id)) : `Ort #${id}`).join(', ')}`));
            if ((item.supporting_unit_ids || []).length) article.append(element('p', `Aufliegende Einheiten zuerst berücksichtigen: ${item.supporting_unit_ids.map(id => getUnit(id) ? unitLabel(getUnit(id)) : id).join(', ')}`));
            for (const content of item.contents || []) {
                const line = element('p', `${content.part_num || ''} · Farbe ${content.color_id ?? 'unbekannt'} · ${content.hint || content.classification || ''}`);
                article.append(line); appendList(article, 'Hinweise zum Inhalt', content.reasons || content.missing || []);
                if ((item.eligible_storage_ids || []).includes(content.storage_id)) {
                    const transfer = element('button', 'Teilumbuchung vorbereiten'); transfer.type = 'button';
                    transfer.addEventListener('click', () => {
                        const form = byId('warehouse-move-form'); form.elements.kind.value = 'quantity'; form.elements.source_storage_id.value = String(content.storage_id);
                        form.scrollIntoView({ block: 'center' }); form.elements.target_unit_id.focus();
                    }); article.append(transfer);
                }
            }
            const choose = element('button', item.whole_box ? 'Ganze Box prüfen und Bewegung vorbereiten' : 'Einheit anzeigen'); choose.type = 'button'; choose.addEventListener('click', () => { byId('warehouse-move-form').elements.kind.value = 'unit'; selectUnit(item.unit_id); }); article.append(choose); box.append(article);
        }
        if (!(report.units || []).length) box.append(element('p', 'Keine belastbaren Prüfkandidaten. Unvollständige Katalog- oder Inhaltsdaten zunächst ergänzen.'));
        appendList(box, 'Offene Angaben', report.missing || []);
    }
    function populateForm(form, record) {
        if (!record) return;
        for (const input of form.elements) {
            if (!input.name || input.name === 'id' || record[input.name] === undefined) continue;
            if (input.type === 'checkbox') input.checked = !!record[input.name];
            else if (input.name === 'height_profile') input.value = record[input.name] ? JSON.stringify(record[input.name]) : '';
            else input.value = record[input.name] ?? '';
        }
    }
    let contentOptionsPending = null;
    async function loadContentOptions() {
        if (state.allContents) return;
        if (!contentOptionsPending) contentOptionsPending = api('/contents').then(result => {
            state.allContents = result.items || []; refreshOptions();
        }).catch(problem => error(problem.message)).finally(() => { contentOptionsPending = null; });
        await contentOptionsPending;
    }
    function initialize() {
        for (const [formId, records] of [
            ['warehouse-location-form', () => state.locations],
            ['warehouse-type-form', () => state.types],
            ['warehouse-content-form', () => state.allContents || state.contents],
            ['warehouse-unit-update-form', () => state.units],
            ['warehouse-planned-set-form', () => state.settings.planned_sets || []]
        ]) {
            const form = byId(formId);
            form.elements.id.addEventListener('change', () => populateForm(form, records().find(item => item.id === Number(form.elements.id.value))));
        }
        bindForm('warehouse-location-form', async data => { const id = data.id; delete data.id; data.height_profile = data.height_profile ? JSON.parse(data.height_profile) : null; await api(id ? `/locations/${id}` : '/locations', id ? 'PATCH' : 'POST', data); });
        bindForm('warehouse-type-form', async data => { const id = data.id; delete data.id; await api(id ? `/types/${id}` : '/types', id ? 'PATCH' : 'POST', data); });
        bindForm('warehouse-unit-form', async data => { await api('/units', 'POST', data); });
        bindForm('warehouse-placement-form', async data => { const id = data.unit_id; delete data.unit_id; if (data.support_unit_id) data.shelf_id = null; await api(`/units/${id}/placement`, 'POST', data); byId('warehouse-placement-form').elements.support_unit_id.value = String(id); byId('warehouse-placement-form').elements.shelf_id.value = ''; byId('warehouse-placement-form').elements.relation_kind.value = 'stacked';
            byId('warehouse-placement-form').elements.x_mm.value = '';
            byId('warehouse-placement-form').elements.depth_offset_mm.value = '';
            byId('warehouse-placement-form').elements.order_left.value = '0'; });
        bindForm('warehouse-rule-form', async data => { await api('/stack-rules', 'POST', data); });
        bindForm('warehouse-unit-update-form', async data => { const id = data.id; delete data.id; await api(`/units/${id}`, 'PATCH', data); });
        bindForm('warehouse-partition-form', async data => { await api(`/units/${data.id}/partitions`, 'POST', { partition_count: data.partition_count }); });
        bindForm('warehouse-content-form', async (data, form) => {
            let id = data.id; delete data.id;
            if (!id) {
                const created = await api('/contents', 'POST', { ...data, quantity: null });
                id = created.id;
                // Preserve the newly created ID before the count request, so retrying
                // a failed count cannot accidentally create another content record.
                state.contents.push(created); refreshOptions(); form.elements.id.value = String(id);
            }
            await api(`/contents/${id}`, 'PATCH', data);
        });
        bindForm('warehouse-category-form', async data => { await api('/category-rules', 'POST', data); });
        bindForm('warehouse-preference-form', async data => { await api('/preferences', 'POST', data); });
        bindForm('warehouse-planned-set-form', async data => { const id = data.id; delete data.id; await api(id ? `/planned-sets/${id}` : '/planned-sets', id ? 'PATCH' : 'POST', data); });
        bindForm('warehouse-settings-form', async data => { await api('/settings', 'POST', data); });
        bindForm('warehouse-search-form', async data => { await showSearch(data); });
        bindForm('warehouse-move-form', async data => {
            const body = { kind: data.kind, idempotency_key: crypto.randomUUID(), reason: data.reason || 'Physische Lagerbewegung', capacity_confirmed: data.capacity_confirmed };
            if (data.kind === 'unit') {
                body.unit_id = data.unit_id; body.target_placement = data.remove ? { remove: true } : { shelf_id: data.support_unit_id ? null : data.shelf_id, support_unit_id: data.support_unit_id, relation_kind: data.relation_kind, order_left: data.order_left, x_mm: data.x_mm, depth_offset_mm: data.depth_offset_mm, orientation: data.orientation };
            }
            else {
                body.target_unit_id = data.target_unit_id; body.quantity = data.quantity;
                if (data.kind === 'quantity') body.storage_id = data.source_storage_id;
                else { body.part_num = data.part_num; body.color_id = data.color_id; }
            }
            await api('/moves', 'POST', body);
        });
        for (const formId of ['warehouse-placement-form', 'warehouse-move-form']) {
            const form = byId(formId);
            form.elements.support_unit_id.addEventListener('change', () => {
                form.elements.x_mm.value = ''; form.elements.depth_offset_mm.value = '';
                if (form.elements.support_unit_id.value) { form.elements.shelf_id.value = ''; form.elements.relation_kind.value = 'stacked'; }
            });
        }
        byId('warehouse-move-preview').addEventListener('click', event => act(event.currentTarget, async () => {
            const data = values(byId('warehouse-move-form'));
            if (data.kind !== 'unit' || !data.unit_id || data.remove) throw new Error('Für die Zielpassung eine Behälterbewegung mit Einheit und Ziel wählen.');
            const result = await api(`/units/${data.unit_id}/preview`, 'POST', { shelf_id: data.support_unit_id ? null : data.shelf_id, support_unit_id: data.support_unit_id, relation_kind: data.relation_kind, order_left: data.order_left, x_mm: data.x_mm, depth_offset_mm: data.depth_offset_mm, orientation: data.orientation });
            const box = byId('warehouse-move-preview-result'); empty(box);
            box.append(element('p', result.status === 'fits' || result.status === 'fit' ? 'Gemessene Zielpassung bestätigt.' : result.status === 'no_fit' ? 'Ziel passt nicht.' : 'Passung ungeprüft – Angaben ergänzen oder vor Ort prüfen.', 'warehouse-note'));
            appendList(box, 'Passprüfung', result.reasons || []);
        }));
        byId('warehouse-seed').addEventListener('click', event => act(event.currentTarget, async () => { await api('/setup', 'POST', {}); await load(); }));
        byId('warehouse-column-rows').addEventListener('change', renderLayout);
        byId('warehouse-refresh').addEventListener('click', event => act(event.currentTarget, load));
        byId('warehouse-archive').addEventListener('click', event => act(event.currentTarget, showArchive));
        byId('warehouse-shelf').addEventListener('change', () => { rememberShelf(); state.selectedLegacyKey = null; state.selectedUnit = null; byId('warehouse-details').replaceChildren(element('p', 'Wähle eine Box aus der Lagerübersicht.')); load().catch(problem => error(problem.message)); });
        document.querySelectorAll('[data-options="contents"]').forEach(select => select.addEventListener('focus', loadContentOptions));
        byId('warehouse-capture').addEventListener('toggle', () => { if (byId('warehouse-capture').open) loadContentOptions(); });
        byId('warehouse-list').addEventListener('click', () => { byId('warehouse-layout').className = 'warehouse-list'; byId('warehouse-list').setAttribute('aria-pressed', 'true'); byId('warehouse-front').setAttribute('aria-pressed', 'false'); });
        byId('warehouse-front').addEventListener('click', () => { byId('warehouse-layout').className = 'warehouse-front'; byId('warehouse-list').setAttribute('aria-pressed', 'false'); byId('warehouse-front').setAttribute('aria-pressed', 'true'); });
        load().then(() => {
            const params = new URLSearchParams(location.search);
            const selected = params.get('unit_id');
            if (selected) selectUnit(selected);
            const part = params.get('part_num');
            if (part) {
                const rawColor = params.get('color_id');
                const color = rawColor !== null && rawColor !== '' && Number.isInteger(Number(rawColor)) ? Number(rawColor) : null;
                const form = byId('warehouse-search-form'); form.elements.part_num.value = part; form.elements.color_id.value = color ?? '';
                showSearch({ part_num: part, color_id: color }).catch(problem => error(problem.message));
            }
        }).catch(problem => { error(problem.message); status('Lager konnte nicht geladen werden. Erneut laden.'); });
    }
    initialize();
}());
