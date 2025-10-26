document.addEventListener("DOMContentLoaded", function () {
  const setsTable = document.getElementById("sets-table");
  const setDetails = document.getElementById("set-details");
  const backToSetsButton = document.getElementById("back-to-sets");

  // Table Sorting Functionality
  let sortDirection = {}; // Track sort direction for each column
  
  function initTableSorting() {
    const table = document.getElementById('sets-table-main');
    if (!table) return;
    
    const headers = table.querySelectorAll('thead th[data-sort]');
    
    headers.forEach(header => {
      header.addEventListener('click', () => {
        const sortKey = header.getAttribute('data-sort');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Toggle sort direction
        sortDirection[sortKey] = sortDirection[sortKey] === 'asc' ? 'desc' : 'asc';
        
        // Update visual indicators
        headers.forEach(h => {
          const icon = h.querySelector('.sort-icon');
          icon.className = 'bi bi-arrow-down-up sort-icon';
        });
        
        const currentIcon = header.querySelector('.sort-icon');
        currentIcon.className = sortDirection[sortKey] === 'asc' 
          ? 'bi bi-arrow-up sort-icon'
          : 'bi bi-arrow-down sort-icon';
        
        // Sort rows
        rows.sort((a, b) => {
          let aVal = '', bVal = '';
          
          switch(sortKey) {
            case 'set_num':
              aVal = a.cells[1].textContent.trim();
              bVal = b.cells[1].textContent.trim();
              break;
            case 'set_name':
              aVal = a.cells[2].textContent.trim();
              bVal = b.cells[2].textContent.trim();
              break;
            case 'theme':
              aVal = a.cells[3].textContent.trim();
              bVal = b.cells[3].textContent.trim();
              break;
            case 'box_id':
              aVal = parseInt(a.cells[4].textContent.trim()) || 0;
              bVal = parseInt(b.cells[4].textContent.trim()) || 0;
              return sortDirection[sortKey] === 'asc' ? aVal - bVal : bVal - aVal;
            case 'parts':
              aVal = parseInt(a.cells[5].textContent.split('/')[1]) || 0;
              bVal = parseInt(b.cells[5].textContent.split('/')[1]) || 0;
              return sortDirection[sortKey] === 'asc' ? aVal - bVal : bVal - aVal;
            case 'status':
              aVal = a.cells[6].querySelector('.status-badge').textContent.trim();
              bVal = b.cells[6].querySelector('.status-badge').textContent.trim();
              break;
            case 'label_printed':
              aVal = a.cells[7].querySelector('input[type="checkbox"]').checked ? 1 : 0;
              bVal = b.cells[7].querySelector('input[type="checkbox"]').checked ? 1 : 0;
              return sortDirection[sortKey] === 'asc' ? aVal - bVal : bVal - aVal;
          }
          
          // String comparison
          if (sortDirection[sortKey] === 'asc') {
            return aVal.localeCompare(bVal, undefined, {numeric: true});
          } else {
            return bVal.localeCompare(aVal, undefined, {numeric: true});
          }
        });
        
        // Reappend sorted rows
        rows.forEach(row => tbody.appendChild(row));
      });
    });
  }
  
  // Enhanced Search and Filter Functionality
  function initSearchAndFilter() {
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
  initTableSorting();
  initSearchAndFilter();

  // Mark all parts as existing
  const markAllExistingButton =
    document.getElementById("mark-all-existing");

  markAllExistingButton.addEventListener("click", () => {
    // Get all input fields in the Non-Spare Parts, Spare Parts, and Minifigs tables
    const partsTables = [
      document.getElementById("non-spare-parts-table-body"),
      document.getElementById("spare-parts-table-body"),
      document.getElementById("minifigs-table-body"),
    ];

    partsTables.forEach((tableBody) => {
      if (tableBody) {
        const rows = tableBody.querySelectorAll("tr");
        rows.forEach((row) => {
          const quantityCell = row.querySelector("td:nth-child(6)"); // Quantity Required cell (6th column)
          const ownedInput = row.querySelector("input[type='number']"); // Owned input field

          if (quantityCell && ownedInput) {
            const quantity = parseInt(
              quantityCell.textContent.trim(),
              10
            );
            if (!isNaN(quantity)) {
              ownedInput.value = quantity; // Set Owned to Quantity
            }
          }
        });
      }
    });

    alert("All parts marked as existing!");
  });

  // Reset all parts to 0
  const resetAllToZeroButton = document.getElementById("reset-all-to-zero");

  resetAllToZeroButton.addEventListener("click", () => {
    // Get all input fields in the Non-Spare Parts, Spare Parts, and Minifigs tables
    const partsTables = [
      document.getElementById("non-spare-parts-table-body"),
      document.getElementById("spare-parts-table-body"),
      document.getElementById("minifigs-table-body"),
    ];

    partsTables.forEach((tableBody) => {
      if (tableBody) {
        const rows = tableBody.querySelectorAll("tr");
        rows.forEach((row) => {
          const ownedInput = row.querySelector("input[type='number']"); // Owned input field

          if (ownedInput) {
            ownedInput.value = 0; // Set Owned to 0
          }
        });
      }
    });

    alert("All parts reset to 0!");
  });

  // Add event listener for mismatched parts filter
  const filterCheckbox = document.getElementById(
    "filter-mismatched-parts"
  );

  filterCheckbox.addEventListener("change", () => {
    const filterRows = (rows) => {
      rows.forEach((row) => {
        const quantityCell = row.querySelector("td:nth-child(6)"); // Quantity Required cell (6th column)
        const ownedInput = row.querySelector("input[type='number']");
        if (quantityCell && ownedInput) {
          const quantity = parseInt(quantityCell.textContent.trim(), 10);
          const owned = parseInt(ownedInput.value.trim(), 10);
          if (filterCheckbox.checked && quantity === owned) {
            row.style.display = "none"; // Hide rows with matching quantities
          } else {
            row.style.display = ""; // Show all rows
          }
        }
      });
    };

    const nonSparePartsRows = document.querySelectorAll(
      "#non-spare-parts-table-body tr"
    );
    const sparePartsRows = document.querySelectorAll(
      "#spare-parts-table-body tr"
    );
    const minifigsRows = document.querySelectorAll(
      "#minifigs-table-body tr"
    );

    filterRows(nonSparePartsRows);
    filterRows(sparePartsRows);
    filterRows(minifigsRows);
  });

  // Handle back to sets button
  backToSetsButton.addEventListener("click", () => {
    // Hide the set details and show the master table
    setDetails.classList.add("hidden");
    setsTable.classList.remove("hidden");

    // Reset the mismatched filter checkbox to unchecked
    filterCheckbox.checked = false;

    // Show all rows (reset filtering)
    const resetFilter = (rows) => {
      rows.forEach((row) => {
        row.style.display = ""; // Show all rows
      });
    };

    const nonSparePartsRows = document.querySelectorAll(
      "#non-spare-parts-table-body tr"
    );
    const sparePartsRows = document.querySelectorAll(
      "#spare-parts-table-body tr"
    );
    const minifigsRows = document.querySelectorAll(
      "#minifigs-table-body tr"
    );

    resetFilter(nonSparePartsRows);
    resetFilter(sparePartsRows);
    resetFilter(minifigsRows);
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
            const colorRgb = part.color_rgb || "FFFFFF";
            const brightness = parseInt(colorRgb, 16);
            const textColor = brightness > 0x888888 ? "black" : "white";

            const partRow = `
                    <tr class="${statusClass}">
                        <td><img src="${part.part_img_url}" alt="${part.name
              }" class="img-thumbnail" width="50" style="cursor: pointer;" onclick="showImageModal('${part.part_img_url}', '${part.name} (${part.part_num})')" /></td>
                        <td>${part.part_num}</td>
                        <td>${part.name}</td>
                        <td>${part.category || "Unknown Category"}</td>
                        <td style="background-color: #${colorRgb}; color: ${textColor};">${part.color || "Not Specified"}</td>
                        <td>${part.quantity}</td>
                        <td>
                            <input type="number" name="part_id_${part.id
              }" value="${part.have_quantity}" min="0" max="${part.quantity
              }" class="form-control">
                        </td>
                        <td>${part.location || "Not Specified"}</td>
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
                                    <td><img src="${minifig.img_url}" alt="${minifig.name}" class="img-thumbnail" width="50" style="cursor: pointer;" onclick="showImageModal('${minifig.img_url}', '${minifig.name} (${minifig.fig_num})')" /></td>
                                    <td>${minifig.fig_num}</td>
                                    <td>${minifig.name}</td>
                                    <td>${minifig.quantity}</td>
                                </tr>`;

            // Minifigure parts row (nested table)
            if (minifig.parts && minifig.parts.length > 0) {
              const partsTableRows = minifig.parts.map(part => {
                // Use table-danger for missing parts, table-success for complete parts
                const statusClass = part.quantity > part.have_quantity ? "table-danger" : "table-success";
                const colorRgb = part.color_rgb || "FFFFFF";
                const brightness = parseInt(colorRgb, 16);
                const textColor = brightness > 0x888888 ? "black" : "white";

                return `
                    <tr class="${statusClass}">
                        <td><img src="${part.part_img_url}" alt="${part.name}" class="img-thumbnail" width="30" style="cursor: pointer;" onclick="showImageModal('${part.part_img_url}', '${part.name} (${part.part_num})')" /></td>
                        <td>${part.part_num}</td>
                        <td>${part.name}</td>
                        <td style="background-color: #${colorRgb}; color: ${textColor};">${part.color || "Not Specified"}</td>
                        <td>${part.quantity}</td>
                        <td>
                            <input type="number" name="minifig_part_id_${part.id}" value="${part.have_quantity}" min="0" max="${part.quantity}" class="form-control">
                        </td>
                        <td>${part.location || "Not Specified"}</td>
                    </tr>`;
              }).join('');

              minifigsTableBody.innerHTML += `
                                <tr>
                                    <td colspan="4">
                                        <h6>Parts for ${minifig.name} (${minifig.quantity} ${minifig.quantity > 1 ? 'minifigures' : 'minifigure'}) - Total quantities shown:</h6>
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
        })
        .catch((error) =>
          console.error("Error fetching User_Set details:", error)
        );
    });
  });

  // Handle back to sets button
  backToSetsButton.addEventListener("click", () => {
    setDetails.classList.add("hidden");
    setsTable.classList.remove("hidden");
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

  // Handle Generate Label
  document.querySelectorAll(".generate-label").forEach((button) => {
    button.addEventListener("click", () => {
      const User_SetId = button.getAttribute("data-user-set-id");
      const boxSize = button.getAttribute("data-box-size");

      fetch("/set_maintain/generate_label", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ set_id: User_SetId, box_size: boxSize }),
      })
        .then((response) => {
          if (response.ok) {
            return response.blob();
          }
          throw new Error("Failed to generate label");
        })
        .then((blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.style.display = "none";
          a.href = url;
          a.download = `${User_SetId}_${boxSize}.drawio`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
        })
        .catch((error) =>
          console.error("Error generating label:", error)
        );
    });
  });
});

// Function to show image in modal
function showImageModal(imageSrc, imageName) {
  document.getElementById('modalImage').src = imageSrc;
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
