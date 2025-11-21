let editModal, deleteModal;
let currentDeleteId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals
    editModal = new bootstrap.Modal(document.getElementById('editModal'));
    deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));

    // Initialize all location selects
    loadLocations();

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
        container.innerHTML = '<div class="alert alert-info">No parts found in this box.</div>';
        return;
    }

    let html = `
        <div class="card shadow-sm">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">Box Contents: ${location} - ${level} - ${box}</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Image</th>
                                <th>Part Number</th>
                                <th>Name</th>
                                <th>Category</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
    `;

    contents.forEach(part => {
        html += `
            <tr>
                <td><img src="${part.img_url}" alt="${part.name}" style="max-width: 60px; height: auto;"></td>
                <td>${part.part_num}</td>
                <td>${part.name}</td>
                <td>${part.category}</td>
                <td>
                    <button class="btn btn-sm btn-warning edit-btn" 
                            data-id="${part.storage_id}" 
                            data-part="${part.part_num}"
                            data-location="${location}"
                            data-level="${level}"
                            data-box="${box}">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-danger delete-btn" 
                            data-id="${part.storage_id}"
                            data-part="${part.part_num}">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `;
    });

    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;

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
