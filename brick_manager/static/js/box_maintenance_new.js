let editModal, deleteModal;
let currentDeleteId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals
    editModal = new bootstrap.Modal(document.getElementById('editModal'));
    deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));

    // Initialize all location selects
    loadLocations();

    // Avery 3474 batch label queue
    setupLabelQueue();

    // Single Box View handlers
    setupSingleBoxView();

    // Location Overview handlers
    setupLocationOverview();

    // Level Overview handlers
    setupLevelOverview();

    // Edit and Delete handlers
    setupEditAndDelete();
});

function loadLocations() {
    fetch('/box_maintenance/filter_data')
        .then(response => response.json())
        .then(data => {
            const selects = [
                document.getElementById('location'),
                document.getElementById('locationOverviewSelect'),
                document.getElementById('levelLocationSelect')
            ];

            selects.forEach(select => {
                data.locations.forEach(location => {
                    const option = document.createElement('option');
                    option.value = location;
                    option.textContent = location;
                    select.appendChild(option);
                });
            });

            // Populate edit modal location select
            const editLocationSelect = document.getElementById('editLocation');
            data.locations.forEach(location => {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = location;
                editLocationSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading locations:', error));
}

function setupSingleBoxView() {
    const locationSelect = document.getElementById('location');
    const levelSelect = document.getElementById('level');
    const boxSelect = document.getElementById('box');
    const form = document.getElementById('singleBoxForm');
    const generateLabelBtn = document.getElementById('generateLabelBtn');

    locationSelect.addEventListener('change', function() {
        levelSelect.disabled = true;
        boxSelect.disabled = true;
        levelSelect.innerHTML = '<option value="">Select Level</option>';
        boxSelect.innerHTML = '<option value="">Select Box</option>';
        generateLabelBtn.disabled = true;

        if (this.value) {
            fetch(`/box_maintenance/filter_data?location=${this.value}`)
                .then(response => response.json())
                .then(data => {
                    data.levels.forEach(level => {
                        const option = document.createElement('option');
                        option.value = level;
                        option.textContent = level;
                        levelSelect.appendChild(option);
                    });
                    levelSelect.disabled = false;
                });
        }
    });

    levelSelect.addEventListener('change', function() {
        boxSelect.disabled = true;
        boxSelect.innerHTML = '<option value="">Select Box</option>';
        generateLabelBtn.disabled = true;

        if (this.value && locationSelect.value) {
            fetch(`/box_maintenance/filter_data?location=${locationSelect.value}&level=${this.value}`)
                .then(response => response.json())
                .then(data => {
                    data.boxes.forEach(box => {
                        const option = document.createElement('option');
                        option.value = box;
                        option.textContent = box;
                        boxSelect.appendChild(option);
                    });
                    boxSelect.disabled = false;
                });
        }
    });

    boxSelect.addEventListener('change', function() {
        generateLabelBtn.disabled = !this.value;
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const location = locationSelect.value;
        const level = levelSelect.value;
        const box = boxSelect.value;

        const container = document.getElementById('singleBoxContents');
        showLoadingSpinner(container, 'Loading box contents...');

        fetch(`/box_maintenance/contents?location=${location}&level=${level}&box=${box}`)
            .then(response => response.json())
            .then(data => {
                displaySingleBoxContents(data, location, level, box);
            })
            .catch(error => {
                console.error('Error loading box contents:', error);
                container.innerHTML = '<div class="alert alert-danger">Error loading box contents. Please try again.</div>';
            });
    });

    generateLabelBtn.addEventListener('click', function() {
        const location = locationSelect.value;
        const level = levelSelect.value;
        const box = boxSelect.value;

        fetch('/box_maintenance/label', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ location, level, box })
        })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `box_label_${box}.jpg`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        });
    });
}

function setupLocationOverview() {
    const viewBtn = document.getElementById('viewLocationBtn');
    viewBtn.addEventListener('click', function() {
        const location = document.getElementById('locationOverviewSelect').value;
        if (!location) return;

        const container = document.getElementById('locationOverviewContents');
        showLoadingSpinner(container, 'Loading location overview...');

        fetch(`/box_maintenance/location_overview/${location}`)
            .then(response => response.json())
            .then(data => {
                displayLocationOverview(data);
            })
            .catch(error => {
                console.error('Error loading location overview:', error);
                container.innerHTML = '<div class="alert alert-danger">Error loading location overview. Please try again.</div>';
            });
    });
}

function setupLevelOverview() {
    const locationSelect = document.getElementById('levelLocationSelect');
    const levelSelect = document.getElementById('levelLevelSelect');
    const viewBtn = document.getElementById('viewLevelBtn');

    locationSelect.addEventListener('change', function() {
        levelSelect.disabled = true;
        levelSelect.innerHTML = '<option value="">Select Level</option>';
        viewBtn.disabled = true;

        if (this.value) {
            fetch(`/box_maintenance/filter_data?location=${this.value}`)
                .then(response => response.json())
                .then(data => {
                    data.levels.forEach(level => {
                        const option = document.createElement('option');
                        option.value = level;
                        option.textContent = level;
                        levelSelect.appendChild(option);
                    });
                    levelSelect.disabled = false;
                });
        }
    });

    levelSelect.addEventListener('change', function() {
        viewBtn.disabled = !this.value;
    });

    viewBtn.addEventListener('click', function() {
        const location = locationSelect.value;
        const level = levelSelect.value;
        if (!location || !level) return;

        const container = document.getElementById('levelOverviewContents');
        showLoadingSpinner(container, 'Loading level overview...');

        fetch(`/box_maintenance/level_overview/${location}/${level}`)
            .then(response => response.json())
            .then(data => {
                displayLevelOverview(data);
            })
            .catch(error => {
                console.error('Error loading level overview:', error);
                container.innerHTML = '<div class="alert alert-danger">Error loading level overview. Please try again.</div>';
            });
    });
}

function displaySingleBoxContents(contents, location, level, box) {
    const container = document.getElementById('singleBoxContents');
    if (contents.length === 0) {
        const message = document.createElement('div');
        message.className = 'alert alert-info';
        message.textContent = 'No parts found in this box.';
        container.replaceChildren(message);
        return;
    }
    const card = document.createElement('div');
    card.className = 'card shadow-sm';
    const header = document.createElement('div');
    header.className = 'card-header bg-primary text-white';
    const heading = document.createElement('h5');
    heading.className = 'mb-0';
    heading.textContent = `Box Contents: ${location} - ${level} - ${box}`;
    header.appendChild(heading);
    const body = document.createElement('div');
    body.className = 'card-body';
    const responsive = document.createElement('div');
    responsive.className = 'table-responsive';
    const table = document.createElement('table');
    table.className = 'table table-hover';
    const tableHead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    ['Image', 'Part Number', 'Name', 'Category', 'Actions'].forEach(label => {
        const cell = document.createElement('th');
        cell.textContent = label;
        headerRow.appendChild(cell);
    });
    tableHead.appendChild(headerRow);
    const tableBody = document.createElement('tbody');
    contents.forEach(part => {
        const row = document.createElement('tr');
        const imageCell = document.createElement('td');
        const image = document.createElement('img');
        image.src = part.img_url;
        image.alt = part.name;
        image.style.cssText = 'max-width: 60px; height: auto;';
        imageCell.appendChild(image);
        row.append(imageCell);
        [part.part_num, part.name, part.category].forEach(value => {
            const cell = document.createElement('td');
            cell.textContent = value;
            row.appendChild(cell);
        });
        const actions = document.createElement('td');
        [['btn-warning edit-btn', 'fas fa-edit', 'Edit'], ['btn-danger delete-btn', 'fas fa-trash', 'Delete']].forEach(([classes, iconClass, label]) => {
            const button = document.createElement('button');
            button.className = `btn btn-sm ${classes}`;
            button.dataset.id = part.storage_id;
            button.dataset.part = part.part_num;
            if (label === 'Edit') Object.assign(button.dataset, { location, level, box });
            const icon = document.createElement('i');
            icon.className = iconClass;
            button.append(icon, document.createTextNode(` ${label}`));
            actions.appendChild(button);
        });
        row.appendChild(actions);
        tableBody.appendChild(row);
    });
    table.append(tableHead, tableBody);
    responsive.appendChild(table);
    body.appendChild(responsive);
    card.append(header, body);
    container.replaceChildren(card);

    // Attach event listeners to edit/delete buttons
    attachActionButtons();
}

function displayLocationOverview(boxes) {
    const container = document.getElementById('locationOverviewContents');
    if (boxes.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No boxes found in this location.</div>';
        return;
    }

    let html = `
        <div class="card shadow-sm">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">Boxes in Location: ${boxes[0].location}</h5>
            </div>
            <div class="card-body">
                <div class="row">
    `;

    boxes.forEach(box => {
        const multiplePartsHtml = box.part_count > 1
            ? `<span class="badge bg-warning text-dark position-absolute top-0 end-0 m-2">+${box.part_count - 1} more</span>`
            : '';

        html += `
            <div class="col-md-4 col-lg-3 mb-3">
                <div class="card h-100 border-success box-card">
                    <div class="position-relative">
                        <img src="${box.img_url}" class="card-img-top" alt="Part preview" style="height: 150px; object-fit: contain; padding: 10px;">
                        ${multiplePartsHtml}
                    </div>
                    <div class="card-body">
                        <h6 class="card-title"><i class="fas fa-box"></i> Level ${box.level} - Box ${box.box}</h6>
                        <p class="card-text">
                            <span class="badge bg-success">${box.part_count} ${box.part_count === 1 ? 'part' : 'parts'}</span>
                        </p>
                        <button class="btn btn-sm btn-primary view-box-btn"
                                data-location="${box.location}"
                                data-level="${box.level}"
                                data-box="${box.box}">
                            View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    });

    html += `
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;

    // Attach click handlers to view buttons
    document.querySelectorAll('.view-box-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const location = this.dataset.location;
            const level = this.dataset.level;
            const box = this.dataset.box;

            // Switch to single box tab and load contents
            document.getElementById('single-box-tab').click();
            document.getElementById('location').value = location;
            document.getElementById('location').dispatchEvent(new Event('change'));

            setTimeout(() => {
                document.getElementById('level').value = level;
                document.getElementById('level').dispatchEvent(new Event('change'));

                setTimeout(() => {
                    document.getElementById('box').value = box;
                    document.getElementById('singleBoxForm').dispatchEvent(new Event('submit'));
                }, 300);
            }, 300);
        });
    });
}

function displayLevelOverview(boxes) {
    const container = document.getElementById('levelOverviewContents');
    if (boxes.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No boxes found in this level.</div>';
        return;
    }

    let html = `
        <div class="card shadow-sm">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">Boxes in ${boxes[0].location} - Level ${boxes[0].level}</h5>
            </div>
            <div class="card-body">
                <div class="row">
    `;

    boxes.forEach(box => {
        const multiplePartsHtml = box.part_count > 1
            ? `<span class="badge bg-warning text-dark position-absolute top-0 end-0 m-2">+${box.part_count - 1} more</span>`
            : '';

        html += `
            <div class="col-md-3 col-lg-2 mb-3">
                <div class="card h-100 border-info box-card">
                    <div class="position-relative">
                        <img src="${box.img_url}" class="card-img-top" alt="Part preview" style="height: 120px; object-fit: contain; padding: 10px;">
                        ${multiplePartsHtml}
                    </div>
                    <div class="card-body text-center">
                        <h5 class="card-title"><i class="fas fa-box"></i> Box ${box.box}</h5>
                        <p class="card-text">
                            <span class="badge bg-info">${box.part_count} ${box.part_count === 1 ? 'part' : 'parts'}</span>
                        </p>
                        <button class="btn btn-sm btn-primary view-box-btn"
                                data-location="${box.location}"
                                data-level="${box.level}"
                                data-box="${box.box}">
                            View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    });

    html += `
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;

    // Attach click handlers
    document.querySelectorAll('.view-box-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const location = this.dataset.location;
            const level = this.dataset.level;
            const box = this.dataset.box;

            document.getElementById('single-box-tab').click();
            document.getElementById('location').value = location;
            document.getElementById('location').dispatchEvent(new Event('change'));

            setTimeout(() => {
                document.getElementById('level').value = level;
                document.getElementById('level').dispatchEvent(new Event('change'));

                setTimeout(() => {
                    document.getElementById('box').value = box;
                    document.getElementById('singleBoxForm').dispatchEvent(new Event('submit'));
                }, 300);
            }, 300);
        });
    });
}

function attachActionButtons() {
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const storageId = this.dataset.id;
            const partNum = this.dataset.part;
            const location = this.dataset.location;
            const level = this.dataset.level;
            const box = this.dataset.box;

            document.getElementById('editStorageId').value = storageId;
            document.getElementById('editPartNum').value = partNum;
            document.getElementById('editPartNumDisplay').value = partNum;
            document.getElementById('editLocation').value = location;
            document.getElementById('editLevel').value = level;
            document.getElementById('editBox').value = box;

            editModal.show();
        });
    });

    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            currentDeleteId = this.dataset.id;
            document.getElementById('deletePartNum').textContent = this.dataset.part;
            deleteModal.show();
        });
    });
}

function setupEditAndDelete() {
    document.getElementById('saveEditBtn').addEventListener('click', function() {
        const storageId = document.getElementById('editStorageId').value;
        const location = document.getElementById('editLocation').value;
        const level = document.getElementById('editLevel').value;
        const box = document.getElementById('editBox').value;

        fetch('/box_maintenance/update_part_location', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                storage_id: storageId,
                location: location,
                level: level,
                box: box
            })
        })
        .then(response => response.json())
        .then(data => {
            editModal.hide();
            alert('Location updated successfully!');
            // Refresh current view
            document.getElementById('singleBoxForm').dispatchEvent(new Event('submit'));
        })
        .catch(error => {
            console.error('Error updating location:', error);
            alert('Error updating location.');
        });
    });

    document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
        fetch(`/box_maintenance/delete_part/${currentDeleteId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            deleteModal.hide();
            alert('Part removed from storage successfully!');
            // Refresh current view
            document.getElementById('singleBoxForm').dispatchEvent(new Event('submit'));
        })
        .catch(error => {
            console.error('Error deleting part:', error);
            alert('Error deleting part.');
        });
    });
}

function showLoadingSpinner(container, message = 'Loading...') {
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3 text-muted">${message}</p>
        </div>
    `;
}

function setupLabelQueue() {
    const queueBody = document.getElementById('label-queue-body');
    const message = document.getElementById('label-queue-message');
    const progress = document.getElementById('label-sheet-progress');
    const startPosition = document.getElementById('label-start-position');
    const horizontalOffset = document.getElementById('label-horizontal-offset');
    const verticalOffset = document.getElementById('label-vertical-offset');
    const selectMissingButton = document.getElementById('select-missing-labels');
    const clearSelectionButton = document.getElementById('clear-label-selection');
    const generateButton = document.getElementById('generate-label-sheet');
    const confirmButton = document.getElementById('confirm-label-sheet');
    const locationFilter = document.getElementById('label-location-filter');
    const levelFilter = document.getElementById('label-level-filter');
    const boxFilter = document.getElementById('label-box-filter');
    const statusFilter = document.getElementById('label-status-filter');
    let boxes = [];
    let downloadedBoxes = [];

    function selectedBoxes() {
        return Array.from(queueBody.querySelectorAll('.label-queue-checkbox:checked'))
            .map(checkbox => boxes[Number(checkbox.dataset.index)]);
    }

    function boxReference(box) {
        return { location: box.location, level: box.level, box: box.box };
    }

    function updateProgress() {
        const selected = selectedBoxes().length;
        const firstSlot = Math.max(1, Math.min(24, Number(startPosition.value) || 1));
        const occupiedSlots = firstSlot - 1 + selected;
        const sheets = selected ? Math.ceil(occupiedSlots / 24) : 0;
        const remaining = selected ? (24 - (occupiedSlots % 24)) % 24 : 25 - firstSlot;
        progress.textContent = selected
            ? `${selected} selected · ${sheets} sheet${sheets === 1 ? '' : 's'} · ${remaining} free on last sheet`
            : `${remaining} free positions on first sheet`;
        generateButton.disabled = selected === 0;
        downloadedBoxes = [];
        confirmButton.disabled = true;
    }

    function selectNextMissingSheet() {
        const firstSlot = Math.max(1, Math.min(24, Number(startPosition.value) || 1));
        let available = 25 - firstSlot;
        queueBody.querySelectorAll('.label-queue-checkbox').forEach(checkbox => {
            const box = boxes[Number(checkbox.dataset.index)];
            const visible = !checkbox.closest('tr').hidden;
            checkbox.checked = visible && !box.label_printed && available > 0;
            if (checkbox.checked) available -= 1;
        });
        updateProgress();
    }

    function clearSelection() {
        queueBody.querySelectorAll('.label-queue-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        updateProgress();
    }

    function populateFilter(select, values, emptyLabel) {
        select.replaceChildren();
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = emptyLabel;
        select.appendChild(emptyOption);
        [...new Set(values)].sort((left, right) =>
            left.localeCompare(right, undefined, { numeric: true })
        ).forEach(value => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = value;
            select.appendChild(option);
        });
    }

    function applyFilters() {
        const location = locationFilter.value;
        const level = levelFilter.value;
        const boxSearch = boxFilter.value.trim().toLowerCase();
        const status = statusFilter.value;
        let visibleCount = 0;
        let visibleMissingCount = 0;

        queueBody.querySelectorAll('tr').forEach(row => {
            const box = boxes[Number(row.dataset.index)];
            const matches = (!location || box.location === location) &&
                (!level || box.level === level) &&
                (!boxSearch || box.box.toLowerCase().includes(boxSearch)) &&
                (!status || (status === 'printed') === box.label_printed);
            row.hidden = !matches;
            if (matches) {
                visibleCount += 1;
                if (!box.label_printed) visibleMissingCount += 1;
            } else {
                row.querySelector('.label-queue-checkbox').checked = false;
            }
        });
        message.className = `alert ${visibleMissingCount ? 'alert-warning' : 'alert-success'} mt-3 mb-0`;
        message.textContent = `${visibleCount} of ${boxes.length} boxes shown · ${visibleMissingCount} missing labels.`;
        updateProgress();
    }

    function renderQueue() {
        queueBody.replaceChildren();
        boxes.forEach((box, index) => {
            const row = document.createElement('tr');
            row.dataset.index = index;
            const checkboxCell = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input label-queue-checkbox';
            checkbox.dataset.index = index;
            checkbox.checked = false;
            checkbox.setAttribute('aria-label', `Print label for box ${box.box}`);
            checkbox.addEventListener('change', updateProgress);
            checkboxCell.appendChild(checkbox);
            row.appendChild(checkboxCell);

            [box.location, box.level, box.box, box.part_count].forEach(value => {
                const cell = document.createElement('td');
                cell.textContent = value;
                row.appendChild(cell);
            });
            const statusCell = document.createElement('td');
            const badge = document.createElement('span');
            badge.className = box.label_printed ? 'badge text-bg-success' : 'badge text-bg-warning';
            badge.textContent = box.label_printed ? 'Printed' : 'Missing';
            statusCell.appendChild(badge);
            row.appendChild(statusCell);
            queueBody.appendChild(row);
        });
        populateFilter(locationFilter, boxes.map(box => box.location), 'All locations');
        populateFilter(levelFilter, boxes.map(box => box.level), 'All levels');
        applyFilters();
    }

    function loadQueue() {
        fetch('/box_maintenance/label_queue')
            .then(response => {
                if (!response.ok) throw new Error('Could not load label queue.');
                return response.json();
            })
            .then(data => {
                boxes = data.boxes.filter(box =>
                    ['location', 'level', 'box'].every(field =>
                        typeof box[field] === 'string' && box[field].trim() !== ''
                    )
                );
                renderQueue();
            })
            .catch(error => {
                message.className = 'alert alert-danger mt-3 mb-0';
                message.textContent = error.message;
            });
    }

    selectMissingButton.addEventListener('click', selectNextMissingSheet);
    clearSelectionButton.addEventListener('click', clearSelection);
    startPosition.addEventListener('change', updateProgress);
    [locationFilter, levelFilter, statusFilter].forEach(filter =>
        filter.addEventListener('change', applyFilters)
    );
    boxFilter.addEventListener('input', applyFilters);

    generateButton.addEventListener('click', function() {
        const selected = selectedBoxes();
        const payload = {
            boxes: selected.map(boxReference),
            start_position: Number(startPosition.value),
            horizontal_offset_mm: Number(horizontalOffset.value),
            vertical_offset_mm: Number(verticalOffset.value)
        };
        generateButton.disabled = true;
        fetch('/box_maintenance/label_sheet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(response => {
                if (!response.ok) throw new Error('Could not generate label sheet.');
                return response.blob();
            })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `avery_3474_box_labels_x${payload.horizontal_offset_mm}_y${payload.vertical_offset_mm}.pdf`;
                link.click();
                URL.revokeObjectURL(url);
                downloadedBoxes = selected.map(boxReference);
                confirmButton.disabled = false;
                message.className = 'alert alert-info mt-3 mb-0';
                message.textContent = 'PDF downloaded. Confirm only after the sheet printed successfully.';
            })
            .catch(error => {
                message.className = 'alert alert-danger mt-3 mb-0';
                message.textContent = error.message;
            })
            .finally(() => {
                generateButton.disabled = selectedBoxes().length === 0;
            });
    });

    confirmButton.addEventListener('click', function() {
        if (!downloadedBoxes.length || !confirm('Did all selected labels print successfully?')) return;
        fetch('/box_maintenance/label_sheet/printed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ boxes: downloadedBoxes })
        })
            .then(response => {
                if (!response.ok) throw new Error('Could not confirm printed labels.');
                return response.json();
            })
            .then(loadQueue)
            .catch(error => {
                message.className = 'alert alert-danger mt-3 mb-0';
                message.textContent = error.message;
            });
    });

    loadQueue();
}
