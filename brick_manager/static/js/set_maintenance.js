const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[character]));

document.addEventListener("DOMContentLoaded", function () {
  const setsTable = document.getElementById("sets-table");
  const setDetails = document.getElementById("set-details");
  const backToSetsButton = document.getElementById("back-to-sets");


  // Enhanced Search and Filter Functionality
  function initSearchAndFilter() {
    // Large collections are filtered by the server so every matching set is
    // considered, not just the currently rendered page.
    if (document.getElementById('set-filters')) return;

    const searchInput = document.getElementById('search-input');
    const statusFilter = document.getElementById('status-filter');
    const setNumberFilter = document.getElementById('set-number-filter');
    const setNameFilter = document.getElementById('set-name-filter');
    const themeFilter = document.getElementById('theme-filter');
    const labelFilter = document.getElementById('label-filter');
    const completionFilter = document.getElementById('completion-filter');
    const clearFiltersBtn = document.getElementById('clear-filters');
    const filterCount = document.getElementById('filter-count');
    const filterChevron = document.getElementById('filter-chevron');

    // Populate theme filter dynamically
    function populateThemeFilter() {
      const table = document.getElementById('sets-table-main');
      if (!table || !themeFilter) return;

      const themes = new Set();
      const rows = table.querySelectorAll('tbody tr');

      rows.forEach(row => {
        const themeCell = row.cells[3];
        if (themeCell) {
          const theme = themeCell.textContent.trim();
          if (theme) themes.add(theme);
        }
      });

      // Clear existing options except "All Themes"
      themeFilter.innerHTML = '<option value="">All Themes</option>';

      // Add theme options alphabetically
      Array.from(themes).sort().forEach(theme => {
        const option = document.createElement('option');
        option.value = theme.toLowerCase();
        option.textContent = theme;
        themeFilter.appendChild(option);
      });
    }

    // Update filter count and chevron
    function updateFilterIndicators() {
      let activeFilters = 0;

      if (searchInput && searchInput.value.trim()) activeFilters++;
      if (statusFilter && statusFilter.value) activeFilters++;
      if (setNumberFilter && setNumberFilter.value.trim()) activeFilters++;
      if (setNameFilter && setNameFilter.value.trim()) activeFilters++;
      if (themeFilter && themeFilter.value) activeFilters++;
      if (labelFilter && labelFilter.value) activeFilters++;
      if (completionFilter && completionFilter.value) activeFilters++;

      if (filterCount) {
        filterCount.textContent = activeFilters;
      }

      // Update chevron based on collapse state
      const advancedFilters = document.getElementById('advancedFilters');
      if (filterChevron && advancedFilters) {
        if (advancedFilters.classList.contains('show')) {
          filterChevron.className = 'bi bi-chevron-up';
        } else {
          filterChevron.className = 'bi bi-chevron-down';
        }
      }
    }

    function filterTable() {
      const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
      const statusValue = statusFilter ? statusFilter.value.toLowerCase() : '';
      const setNumValue = setNumberFilter ? setNumberFilter.value.toLowerCase() : '';
      const setNameValue = setNameFilter ? setNameFilter.value.toLowerCase() : '';
      const themeValue = themeFilter ? themeFilter.value.toLowerCase() : '';
      const labelValue = labelFilter ? labelFilter.value : '';
      const completionValue = completionFilter ? completionFilter.value : '';
      const table = document.getElementById('sets-table-main');

      if (!table) return;

      const rows = table.querySelectorAll('tbody tr');

      rows.forEach(row => {
        const setNum = row.cells[1].textContent.toLowerCase();
        const setName = row.cells[2].textContent.toLowerCase();
        const theme = row.cells[3].textContent.toLowerCase();
        const statusBadge = row.cells[6].querySelector('.status-badge');
        const status = statusBadge ? statusBadge.textContent.toLowerCase() : '';
        const labelCheckbox = row.cells[7].querySelector('input[type="checkbox"]');
        const isLabelPrinted = labelCheckbox ? labelCheckbox.checked : false;

        // Parse parts completion
        const partsCell = row.cells[5];
        const partsText = partsCell ? partsCell.textContent.trim() : '';
        const partsMatch = partsText.match(/(\d+)\/(\d+)/);
        let completionPercentage = 0;
        if (partsMatch) {
          const owned = parseInt(partsMatch[1]);
          const total = parseInt(partsMatch[2]);
          completionPercentage = total > 0 ? (owned / total) * 100 : 0;
        }

        // Apply filters
        const matchesSearch = !searchTerm ||
          setNum.includes(searchTerm) ||
          setName.includes(searchTerm) ||
          theme.includes(searchTerm);

        const matchesStatus = !statusValue || status.includes(statusValue);
        const matchesSetNum = !setNumValue || setNum.includes(setNumValue);
        const matchesSetName = !setNameValue || setName.includes(setNameValue);
        const matchesTheme = !themeValue || theme.includes(themeValue);

        const matchesLabel = !labelValue ||
          (labelValue === 'printed' && isLabelPrinted) ||
          (labelValue === 'not-printed' && !isLabelPrinted);

        const matchesCompletion = !completionValue ||
          (completionValue === 'complete' && completionPercentage >= 100) ||
          (completionValue === 'incomplete' && completionPercentage > 0 && completionPercentage < 100) ||
          (completionValue === 'no-parts' && completionPercentage === 0);

        const isVisible = matchesSearch && matchesStatus && matchesSetNum &&
                         matchesSetName && matchesTheme && matchesLabel && matchesCompletion;

        row.style.display = isVisible ? '' : 'none';
      });

      updateFilterIndicators();
    }

    // Clear all filters
    function clearAllFilters() {
      if (searchInput) searchInput.value = '';
      if (statusFilter) statusFilter.value = '';
      if (setNumberFilter) setNumberFilter.value = '';
      if (setNameFilter) setNameFilter.value = '';
      if (themeFilter) themeFilter.value = '';
      if (labelFilter) labelFilter.value = '';
      if (completionFilter) completionFilter.value = '';

      filterTable();
    }

    // Event listeners
    if (searchInput) searchInput.addEventListener('input', filterTable);
    if (statusFilter) statusFilter.addEventListener('change', filterTable);
    if (setNumberFilter) setNumberFilter.addEventListener('input', filterTable);
    if (setNameFilter) setNameFilter.addEventListener('input', filterTable);
    if (themeFilter) themeFilter.addEventListener('change', filterTable);
    if (labelFilter) labelFilter.addEventListener('change', filterTable);
    if (completionFilter) completionFilter.addEventListener('change', filterTable);
    if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', clearAllFilters);

    // Handle collapse events for chevron
    const advancedFilters = document.getElementById('advancedFilters');
    if (advancedFilters) {
      advancedFilters.addEventListener('shown.bs.collapse', updateFilterIndicators);
      advancedFilters.addEventListener('hidden.bs.collapse', updateFilterIndicators);
    }

    // Initialize
    populateThemeFilter();
    updateFilterIndicators();
  }

  // Initialize sorting and filtering
  initSearchAndFilter();

  // Older open list pages can still use the inline editor with this asset.
  const filterCheckbox = document.getElementById("filter-mismatched-parts");
  function filterLegacyParts() {
    setDetails.querySelectorAll('.auto-save-quantity').forEach(input => {
      input.closest('tr').hidden = filterCheckbox.checked && input.value === input.dataset.required;
    });
  }
  filterCheckbox?.addEventListener('change', filterLegacyParts);
  function setLegacyQuantities(complete) {
    setDetails.querySelectorAll('.auto-save-quantity').forEach(input => {
      input.value = complete ? input.dataset.required : '0';
      quantitySaveFeedback(input, 'unsaved', 'Änderung noch nicht gespeichert.');
    });
    filterLegacyParts();
  }
  document.getElementById('mark-all-existing')?.addEventListener('click', () => setLegacyQuantities(true));
  document.getElementById('reset-all-to-zero')?.addEventListener('click', () => {
    if (window.confirm('Alle Mengen einschließlich ausgeblendeter Zeilen auf 0 setzen?')) setLegacyQuantities(false);
  });

  // Handle view details
  document.querySelectorAll(".view-details").forEach((button) => {
    button.addEventListener("click", () => {
      const User_SetId = button.getAttribute("data-user-set-id");
      fetch(`/set_maintain/${User_SetId}`)
        .then((response) => response.json())
        .then((data) => {
          setDetails.classList.remove("hidden");
          setsTable.classList.add("hidden");
          window.scrollTo({ top: setDetails.offsetTop, behavior: "smooth" });
          document.getElementById("user-set-id").value = User_SetId;

          // Populate Parts Table (Split into Non-Spare and Spare Parts)
          const nonSparePartsTableBody = document.getElementById(
            "non-spare-parts-table-body"
          );
          const sparePartsTableBody = document.getElementById(
            "spare-parts-table-body"
          );

          nonSparePartsTableBody.innerHTML = "";
          sparePartsTableBody.innerHTML = "";

          data.parts.forEach((part) => {
            // Use table-danger for missing parts, table-success for complete parts
            const statusClass = part.quantity > part.have_quantity ? "table-danger" : "table-success";

            // Determine text color based on background color brightness
            const colorRgb = /^[0-9a-f]{6}$/i.test(part.color_rgb || "") ? part.color_rgb : "FFFFFF";
            const brightness = parseInt(colorRgb, 16);
            const textColor = brightness > 0x888888 ? "black" : "white";

            const partRow = `
                    <tr class="${statusClass}">
                        <td><img src="${escapeHtml(part.part_img_url)}" alt="${escapeHtml(part.name)
              }" data-image-src="${escapeHtml(part.part_img_url)}" data-image-name="${escapeHtml(`${part.name} (${part.part_num})`)}" class="img-thumbnail set-image-clickable" width="50" style="cursor: pointer;" /></td>
                        <td>${escapeHtml(part.part_num)}</td>
                        <td>${escapeHtml(part.name)}</td>
                        <td>${escapeHtml(part.category || "Unknown Category")}</td>
                        <td style="background-color: #${colorRgb}; color: ${textColor};">${escapeHtml(part.color || "Not Specified")}</td>
                        <td>${escapeHtml(part.quantity)}</td>
                        <td>
                            <input type="number" name="part_id_${part.id
              }" value="${part.have_quantity}" min="0" max="${part.quantity
              }" class="form-control auto-save-quantity" data-required="${part.quantity}" data-part-id="${part.id}" data-part-type="regular" enterkeyhint="next">
                        </td>
                        <td>${escapeHtml(part.location || "Not Specified")}</td>
                    </tr>`;

            if (part.is_spare) {
              sparePartsTableBody.innerHTML += partRow;
            } else {
              nonSparePartsTableBody.innerHTML += partRow;
            }
          });

          // Populate Minifigures Table with their parts
          const minifigsTableBody = document.getElementById(
            "minifigs-table-body"
          );
          minifigsTableBody.innerHTML = "";
          data.minifigs.forEach((minifig) => {
            // Main minifigure row
            minifigsTableBody.innerHTML += `
                                <tr>
                                    <td><img src="${escapeHtml(minifig.img_url)}" alt="${escapeHtml(minifig.name)}" data-image-src="${escapeHtml(minifig.img_url)}" data-image-name="${escapeHtml(`${minifig.name} (${minifig.fig_num})`)}" class="img-thumbnail set-image-clickable" width="50" style="cursor: pointer;" /></td>
                                    <td>${escapeHtml(minifig.fig_num)}</td>
                                    <td>${escapeHtml(minifig.name)}</td>
                                    <td>${minifig.quantity}</td>
                                </tr>`;

            // Minifigure parts row (nested table)
            if (minifig.parts && minifig.parts.length > 0) {
              const partsTableRows = minifig.parts.map(part => {
                // Use table-danger for missing parts, table-success for complete parts
                const statusClass = part.quantity > part.have_quantity ? "table-danger" : "table-success";
                const colorRgb = /^[0-9a-f]{6}$/i.test(part.color_rgb || "") ? part.color_rgb : "FFFFFF";
                const brightness = parseInt(colorRgb, 16);
                const textColor = brightness > 0x888888 ? "black" : "white";

                return `
                    <tr class="${statusClass}">
                        <td><img src="${escapeHtml(part.part_img_url)}" alt="${escapeHtml(part.name)}" data-image-src="${escapeHtml(part.part_img_url)}" data-image-name="${escapeHtml(`${part.name} (${part.part_num})`)}" class="img-thumbnail set-image-clickable" width="30" style="cursor: pointer;" /></td>
                        <td>${escapeHtml(part.part_num)}</td>
                        <td>${escapeHtml(part.name)}</td>
                        <td style="background-color: #${colorRgb}; color: ${textColor};">${escapeHtml(part.color || "Not Specified")}</td>
                        <td>${part.quantity}</td>
                        <td>
                            <input type="number" name="minifig_part_id_${part.id}" value="${part.have_quantity}" min="0" max="${part.quantity}" class="form-control auto-save-quantity" data-required="${part.quantity}" data-part-id="${part.id}" data-part-type="minifig" enterkeyhint="next">
                        </td>
                        <td>${escapeHtml(part.location || "Not Specified")}</td>
                    </tr>`;
              }).join('');

              minifigsTableBody.innerHTML += `
                                <tr>
                                    <td colspan="4">
                                        <h6>Parts for ${escapeHtml(minifig.name)} (${minifig.quantity} ${minifig.quantity > 1 ? 'minifigures' : 'minifigure'}) - Total quantities shown:</h6>
                                        <table class="table table-sm table-bordered">
                                            <thead>
                                                <tr>
                                                    <th>Image</th>
                                                    <th>Part Number</th>
                                                    <th>Name</th>
                                                    <th>Color</th>
                                                    <th>Total Quantity</th>
                                                    <th>Owned</th>
                                                    <th>Location</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${partsTableRows}
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>`;
            }
          });

          document.getElementById("status").value = data.status;

          // Attach auto-save listeners to all quantity inputs after all tables are populated
          attachAutoSaveListeners();
        })
        .catch((error) =>
          console.error("Error fetching User_Set details:", error)
        );
    });
  });

  // Handle back to sets button
  backToSetsButton?.addEventListener("click", () => {
    setDetails.classList.add("hidden");
    setsTable.classList.remove("hidden");
    filterCheckbox.checked = false;
  });

  // Confirmation dialog for delete
  document.querySelectorAll(".delete-form").forEach((form) => {
    form.addEventListener("submit", function (event) {
      const confirmDeletion = confirm(
        "Are you sure you want to delete this set? This action cannot be undone."
      );
      if (!confirmDeletion) {
        event.preventDefault();
      }
    });
  });

  const statusModalElement = document.getElementById("statusModal");
  const statusSelect = document.getElementById("statusModalSelect");
  const confirmStatusButton = document.getElementById("confirmStatusChange");
  const statusError = document.getElementById("statusUpdateError");
  let activeStatusButton = null;

  document.querySelectorAll(".change-set-status").forEach((button) => {
    button.addEventListener("click", () => {
      activeStatusButton = button;
      statusSelect.value = button.dataset.currentStatus;
      statusError.classList.add("d-none");
      bootstrap.Modal.getOrCreateInstance(statusModalElement).show();
    });
  });

  confirmStatusButton.addEventListener("click", () => {
    if (!activeStatusButton || statusSelect.value === activeStatusButton.dataset.currentStatus) {
      bootstrap.Modal.getInstance(statusModalElement).hide();
      return;
    }

    confirmStatusButton.disabled = true;
    const formData = new URLSearchParams({
      user_set_id: activeStatusButton.dataset.userSetId,
      status: statusSelect.value
    });
    fetch("/set_maintain/update", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData
    })
      .then((response) => {
        if (!response.ok) throw new Error("Status update failed");
        window.location.reload();
      })
      .catch((error) => {
        statusError.textContent = error.message;
        statusError.classList.remove("d-none");
        confirmStatusButton.disabled = false;
      });
  });

  // Handle Generate Label
  document.querySelectorAll(".generate-label").forEach((button) => {
    button.addEventListener("click", async () => {
      const User_SetId = button.getAttribute("data-user-set-id");
      const boxSize = button.getAttribute("data-box-size");
      const row = button.closest("tr");
      const buttons = row.querySelectorAll(".generate-label");
      const feedback = row.querySelector(".set-label-feedback");
      buttons.forEach(item => { item.disabled = true; });
      feedback.classList.remove("text-danger", "text-success", "text-warning");
      feedback.textContent = "Creating PDF…";
      try {
        const response = await fetch("/set_maintain/generate_label", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ set_id: User_SetId, box_size: boxSize }),
        });
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.error || "Could not create label. Please try again.");
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.style.display = "none";
        link.href = url;
        link.download = `${User_SetId}_${boxSize}.pdf`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
        const status = row.querySelector(".set-label-status");
        status.querySelector(".set-label-printed-checkbox").checked = true;
        const icon = status.querySelector("i");
        icon.className = "bi bi-check-circle-fill text-success";
        icon.title = "Label Printed";
        const description = status.querySelector("small");
        description.className = "text-success";
        description.textContent = "Printed";
        const warning = response.headers.get("X-Label-Warning");
        feedback.classList.add(warning ? "text-warning" : "text-success");
        feedback.textContent = "PDF ready. Print at 100% / actual size." + (warning ? ` ${warning}` : "");
      } catch (error) {
        feedback.classList.add("text-danger");
        feedback.textContent = error.message || "Could not create label. Please try again.";
      } finally {
        buttons.forEach(item => { item.disabled = false; });
      }
    });
  });
});

// Function to show image in modal
function showImageModal(imageSrc, imageName) {
  let safeImageSrc = '/static/default_image.png';
  try {
    const parsedUrl = new URL(imageSrc, window.location.origin);
    if (parsedUrl.protocol === 'https:' || parsedUrl.protocol === 'http:') {
      safeImageSrc = parsedUrl.href;
    }
  } catch (error) {
    console.warn('Rejected invalid image URL', error);
  }
  document.getElementById('modalImage').src = safeImageSrc;
  document.getElementById('modalImageName').textContent = imageName;
  document.getElementById('imageModalLabel').textContent = imageName + ' - Image';
  var imageModal = new bootstrap.Modal(document.getElementById('imageModal'));
  imageModal.show();
}

// Add event listeners for set label printed checkboxes
const setLabelCheckboxes = document.querySelectorAll('.set-label-printed-checkbox');
console.log('Found', setLabelCheckboxes.length, 'set label checkboxes');

setLabelCheckboxes.forEach(checkbox => {
  console.log('Adding event listener to checkbox:', checkbox);
  checkbox.addEventListener('change', function () {
    const userSetId = this.getAttribute('data-user-set-id');
    const isChecked = this.checked;

    console.log('Checkbox changed:', { userSetId, isChecked });

    // Update the database
    fetch('/set_maintain/update_label_status', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_set_id: parseInt(userSetId),
        label_printed: isChecked
      })
    })
      .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Set label status updated:', data);
        // Optional: Show success feedback
        // You could add a small toast notification here
      })
      .catch(error => {
        console.error('Error updating set label status:', error);
        // Revert the checkbox state on error
        this.checked = !isChecked;
        alert('Failed to update label status. Please try again.');
      });
  });
});

// Add event listeners for clickable set images in the master list
document.addEventListener('click', function(event) {
  if (event.target.classList.contains('set-image-clickable')) {
    const imageSrc = event.target.getAttribute('data-image-src');
    const imageName = event.target.getAttribute('data-image-name');
    showImageModal(imageSrc, imageName);
  }
});

// Location editing functionality
document.addEventListener('DOMContentLoaded', function() {
  // Add click handlers to location cells
  function addLocationClickHandlers() {
    // Target location cells in non-spare parts, spare parts, and minifig parts tables
    const locationCells = document.querySelectorAll(
      '#non-spare-parts-table-body tr td:nth-child(8), ' +
      '#spare-parts-table-body tr td:nth-child(8), ' +
      '#minifigs-table-body table tbody tr td:nth-child(7)'
    );

    locationCells.forEach(cell => {
      cell.style.cursor = 'pointer';
      cell.title = 'Click to edit location';

      cell.addEventListener('click', function() {
        const row = this.closest('tr');
        const partNumCell = row.querySelector('td:nth-child(2)');
        const partNameCell = row.querySelector('td:nth-child(3)');

        if (!partNumCell || !partNameCell) return;

        const partNum = partNumCell.textContent.trim();
        const partName = partNameCell.textContent.trim();
        const currentLocation = this.textContent.trim();

        // Parse current location (format: "Location Level-Box" or "Not Specified")
        let location = '', level = '', box = '';
        if (currentLocation !== 'Not Specified') {
          const parts = currentLocation.split(' ');
          if (parts.length >= 1) location = parts[0];
          if (parts.length >= 2) {
            const levelBox = parts[1].split('-');
            level = levelBox[0] || '';
            box = levelBox[1] || '';
          }
        }

        // Populate modal
        document.getElementById('modalPartNum').textContent = partNum;
        document.getElementById('modalPartName').textContent = partName;
        document.getElementById('modalLocation').value = location;
        document.getElementById('modalLevel').value = level;
        document.getElementById('modalBox').value = box;

        // Store reference to the cell for updating later
        const modal = document.getElementById('locationModal');
        modal.setAttribute('data-current-cell', '');
        modal.currentCell = this;
        modal.currentPartNum = partNum;

        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
      });
    });
  }

  // Save location button handler
  const saveLocationBtn = document.getElementById('saveLocationBtn');
  if (saveLocationBtn) {
    saveLocationBtn.addEventListener('click', function() {
      const modal = document.getElementById('locationModal');
      const partNum = modal.currentPartNum;
      const location = document.getElementById('modalLocation').value.trim();
      const level = document.getElementById('modalLevel').value.trim();
      const box = document.getElementById('modalBox').value.trim();
      const statusDiv = document.getElementById('locationUpdateStatus');

      // Clear previous status
      statusDiv.style.display = 'none';
      statusDiv.className = 'alert';

      // Send update request
      fetch('/update_part_location', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          part_num: partNum,
          location: location,
          level: level,
          box: box
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Update the cell text
          if (modal.currentCell) {
            modal.currentCell.textContent = data.location || 'Not Specified';
          }

          // Show success message
          statusDiv.className = 'alert alert-success';
          statusDiv.textContent = data.message;
          statusDiv.style.display = 'block';

          // Close modal after short delay
          setTimeout(() => {
            bootstrap.Modal.getInstance(modal).hide();
            statusDiv.style.display = 'none';
          }, 1500);
        } else {
          // Show error message
          statusDiv.className = 'alert alert-danger';
          statusDiv.textContent = data.message || 'Failed to update location';
          statusDiv.style.display = 'block';
        }
      })
      .catch(error => {
        console.error('Error updating location:', error);
        statusDiv.className = 'alert alert-danger';
        statusDiv.textContent = 'Network error. Please try again.';
        statusDiv.style.display = 'block';
      });
    });
  }

  // Initialize handlers when viewing set details
  const originalViewDetails = document.querySelectorAll('.view-details');
  originalViewDetails.forEach(button => {
    button.addEventListener('click', function() {
      // Wait for the parts tables to be populated
      setTimeout(addLocationClickHandlers, 500);
    });
  });
});

// Handle hardware-keyboard Tab consistently, including iPad browsers.
function isTabKey(event) {
  return event.key === 'Tab'
    || event.key === 'UIKeyInputTab'
    || event.code === 'Tab'
    || event.keyCode === 9
    || event.which === 9
    || event.keyIdentifier === 'U+0009';
}

function isEnterKey(event) {
  return event.key === 'Enter'
    || event.code === 'Enter'
    || event.code === 'NumpadEnter'
    || event.keyCode === 13
    || event.which === 13;
}

function getQuantityInputs(input) {
  const details = input.closest('#set-details');
  if (!details) return [];
  return Array.from(details.querySelectorAll('.auto-save-quantity'))
    .filter(candidate => !candidate.disabled && !candidate.readOnly && candidate.getClientRects().length > 0);
}

function focusAdjacentQuantityInput(input, backwards = false) {
  const inputs = getQuantityInputs(input);
  const index = inputs.indexOf(input);
  if (index < 0) return false;
  const nextInput = inputs[index + (backwards ? -1 : 1)];
  if (!nextInput) return false;
  nextInput.focus();
  if (typeof nextInput.select === 'function') nextInput.select();
  return true;
}

function navigateQuantityInputs(event) {
  if (!isTabKey(event) || event.metaKey || event.isComposing) return;
  // WebKit can incorrectly report Ctrl while Caps Lock is active on an iPad
  // hardware keyboard. Preserve the real Ctrl+Tab browser shortcut.
  const capsLockActive = typeof event.getModifierState === 'function'
    && event.getModifierState('CapsLock');
  if (event.ctrlKey && !capsLockActive) return;
  const input = event.target;
  if (!input.matches('.auto-save-quantity')) return;

  // Keep native navigation at either end so focus can leave the table.
  const inputs = getQuantityInputs(input);
  const index = inputs.indexOf(input);
  if (index < 0 || !inputs[index + (event.shiftKey ? -1 : 1)]) return;
  event.preventDefault();
  // Moving focus commits the edit through the existing change/autosave listener.
  focusAdjacentQuantityInput(input, event.shiftKey);
  const nextInput = document.activeElement;
  // iPad WebKit may apply its native focus action after the key event. Reassert
  // our target once that action has completed, but only if it displaced focus.
  setTimeout(() => {
    if (document.activeElement !== nextInput) nextInput.focus();
  }, 0);
}

document.addEventListener('keydown', navigateQuantityInputs, true);

// Serialize writes by logical part, including when the details table is rebuilt.
const quantitySaveStates = new Map();

function quantitySaveKey(input) {
  return `${input.getAttribute('data-part-type')}:${input.getAttribute('data-part-id')}`;
}

function quantitySaveFeedback(input, state, message) {
  input.dataset.quantitySaveStatus = state;
  input.style.borderColor = state === 'saved' ? '#28a745' : state === 'saving' ? '#ffc107' : '#dc3545';
  input.setAttribute('aria-busy', state === 'saving' ? 'true' : 'false');
  const parent = input.parentElement;
  if (!parent) return;
  let status = parent.querySelector('.quantity-save-status');
  if (!status) {
    status = document.createElement('span');
    status.className = 'quantity-save-status small d-block mt-1';
    status.id = `quantity-save-${quantitySaveKey(input).replace(':', '-')}`;
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    parent.append(status);
    const describedBy = input.getAttribute('aria-describedby') || '';
    input.setAttribute('aria-describedby', `${describedBy} ${status.id}`.trim());
    const retry = document.createElement('button');
    retry.type = 'button'; retry.className = 'quantity-save-retry btn btn-link btn-sm p-0';
    retry.textContent = 'Erneut speichern';
    retry.addEventListener('click', () => saveQuantity(input));
    parent.append(retry);
  }
  status.textContent = message;
  parent.querySelector('.quantity-save-retry').hidden = state !== 'error';
}

async function drainQuantitySaves(state, key) {
  try {
    while (state.latest) {
      const requested = state.latest;
      let data;
      try {
        const response = await fetch('/set_maintain/update_part_quantity', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ part_id: requested.input.getAttribute('data-part-id'),
            part_type: requested.input.getAttribute('data-part-type'), have_quantity: requested.value })
        });
        data = await response.json();
        if (!response.ok || !data.success || !Number.isSafeInteger(data.have_quantity)
          || !Number.isSafeInteger(data.total_quantity)) throw new Error('Save failed');
      } catch (_) {
        if (state.latest && state.latest.value !== requested.value) continue;
        if (state.latest) quantitySaveFeedback(state.latest.input, 'error', 'Nicht gespeichert. Bitte erneut versuchen.');
        return false;
      }
      const current = state.latest;
      if (!current) return false; // A newer invalid edit must remain visible.
      current.input.dataset.lastSavedValue = String(data.have_quantity);
      if (current.value !== requested.value) continue;
      if (Number(current.input.value) !== requested.value || current.input.value.trim() === '') {
        quantitySaveFeedback(current.input, 'unsaved', 'Änderung noch nicht gespeichert.');
        return false;
      }
      current.input.value = String(data.have_quantity);
      const row = current.input.closest('tr');
      if (row) row.className = data.have_quantity >= data.total_quantity ? 'table-success' : 'table-danger';
      quantitySaveFeedback(current.input, 'saved', 'Gespeichert.');
      state.latest = null;
      return true;
    }
    return false;
  } finally {
    quantitySaveStates.delete(key);
  }
}

function saveQuantity(input) {
  const raw = input.value.trim();
  const value = Number(raw);
  const maximum = input.max === undefined || input.max === '' ? Infinity : Number(input.max);
  const key = quantitySaveKey(input);
  let state = quantitySaveStates.get(key);
  if (!/^\d+$/.test(raw) || !Number.isSafeInteger(value) || value < 0 || value > maximum) {
    if (state) state.latest = null;
    const message = 'Bitte eine ganze Menge zwischen 0 und der benötigten Anzahl eingeben.';
    input.setAttribute('aria-invalid', 'true');
    input.setCustomValidity(message);
    quantitySaveFeedback(input, 'invalid', message);
    return Promise.resolve(false);
  }
  input.removeAttribute('aria-invalid');
  input.setCustomValidity('');
  quantitySaveFeedback(input, 'saving', 'Wird gespeichert …');
  if (state) {
    state.latest = { input, value };
    return state.promise;
  }
  state = { latest: { input, value }, promise: null };
  quantitySaveStates.set(key, state);
  state.promise = drainQuantitySaves(state, key);
  return state.promise;
}

function saveAndMoveFromQuantityInput(input, backwards = false) {
  // Duplicate key events share the write; changed values still update its queue.
  const saved = saveQuantity(input);
  if (input.dataset.quantitySavePending === 'true') return saved;
  input.dataset.quantitySavePending = 'true';
  return saved.then(success => {
    if (success) focusAdjacentQuantityInput(input, backwards);
    return success;
  }).finally(() => { delete input.dataset.quantitySavePending; });
}

function handleQuantityEnter(event) {
  const input = event.target;
  if (!input || typeof input.matches !== 'function') return;
  if (!input.matches('.auto-save-quantity') || event.isComposing) return;
  if (!isEnterKey(event)) return;
  event.preventDefault();
  event.stopPropagation();
  saveAndMoveFromQuantityInput(input, event.shiftKey);
}

// Safari on iPad can trigger implicit form submission through keypress even
// when keydown has already been handled. Capture both event variants before
// the containing set form sees them.
document.addEventListener('keydown', handleQuantityEnter, true);
document.addEventListener('keypress', handleQuantityEnter, true);

// Final safeguard for iPadOS versions that submit the form without exposing a
// usable Enter key event. An explicit click on "Save Changes" still works
// because the submit button, rather than a quantity input, is then active.
function waitForQuantitySavesBeforeSubmit(event) {
  const form = event.target;
  if (!form || typeof form.closest !== 'function' || !form.closest('#set-details')) return;
  const pendingInputs = Array.from(form.querySelectorAll('.auto-save-quantity'))
    .filter(input => quantitySaveStates.has(quantitySaveKey(input)));
  if (!pendingInputs.length) return;
  event.preventDefault(); event.stopPropagation();
  if (form.dataset.quantityFormPending === 'true') return;
  form.dataset.quantityFormPending = 'true';
  const submitter = event.submitter;
  const originalSet = form.querySelector('[name="user_set_id"]')?.value;
  if (submitter) submitter.disabled = true;
  Promise.all(pendingInputs.map(saveQuantity)).finally(() => {
    delete form.dataset.quantityFormPending;
    if (submitter) submitter.disabled = false;
  }).then(saved => {
    if (!saved.every(Boolean) || form.isConnected === false
      || originalSet !== form.querySelector('[name="user_set_id"]')?.value
      || form.closest('#set-details')?.classList?.contains('hidden')) return;
    // Re-enter the normal handler to catch writes begun while we were waiting.
    form.dataset.quantityFormResubmit = 'true';
    form.requestSubmit(submitter);
    delete form.dataset.quantityFormResubmit;
  });
}

document.addEventListener('submit', event => {
  const form = event.target;
  const resumed = form && form.dataset && form.dataset.quantityFormResubmit === 'true';
  if (resumed) delete form.dataset.quantityFormResubmit;
  const input = document.activeElement;
  if (!resumed && input && typeof input.matches === 'function'
    && input.matches('.auto-save-quantity') && input.closest('#set-details')) {
    event.preventDefault(); event.stopPropagation(); saveAndMoveFromQuantityInput(input);
    return;
  }
  waitForQuantitySavesBeforeSubmit(event);
}, true);

// Auto-save function for quantity inputs
function attachAutoSaveListeners() {
  document.querySelectorAll('.auto-save-quantity').forEach(input => {
    // Remove any existing listeners to prevent duplicates
    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);

    newInput.dataset.lastSavedValue = newInput.value;

    newInput.addEventListener('change', function() {
      if (this.dataset.lastSavedValue !== this.value) saveQuantity(this);
    });

  });
}
