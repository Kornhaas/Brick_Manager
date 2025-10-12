document.addEventListener("DOMContentLoaded", function () {
    const locationDropdown = document.getElementById("location");
    const levelDropdown = document.getElementById("level");
    const boxDropdown = document.getElementById("box");
    const contentsContainer = document.getElementById("contents-container");
    const boxForm = document.getElementById("box-selection-form");
    const labelButton = document.getElementById("generate-label");

    // Fetch and populate initial dropdown options
    fetch("/box_maintenance/data")
        .then((response) => {
            if (!response.ok) {
                throw new Error(`Failed to fetch dropdown data: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            if (data.error) {
                alert(data.error);
                return;
            }
            populateDropdown(locationDropdown, data.locations);
            populateDropdown(levelDropdown, []); // Start empty
            populateDropdown(boxDropdown, []); // Start empty
        })
        .catch((error) => {
            console.error("Error fetching dropdown data:", error);
            alert("Failed to load dropdown options. Please try again.");
        });

    // Helper function to populate dropdowns
    function populateDropdown(dropdown, options) {
        dropdown.innerHTML = '<option value="" disabled selected>Select an option</option>';
        if (options.length === 0) {
            dropdown.innerHTML += '<option value="" disabled>No options available</option>';
        }
        options.forEach((option) => {
            const opt = document.createElement("option");
            opt.value = option;
            opt.textContent = option;
            dropdown.appendChild(opt);
        });
    }

    // Handle location change
    locationDropdown.addEventListener("change", function () {
        const location = locationDropdown.value;
        if (!location) return;

        // Clear dependent dropdowns
        populateDropdown(levelDropdown, []);
        populateDropdown(boxDropdown, []);

        fetch("/box_maintenance/filter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ location }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Failed to fetch levels: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                    return;
                }
                populateDropdown(levelDropdown, data.levels || []);
            })
            .catch((error) => {
                console.error("Error filtering levels:", error);
                alert("Failed to filter levels. Please try again.");
            });
    });

    // Handle level change
    levelDropdown.addEventListener("change", function () {
        const location = locationDropdown.value;
        const level = levelDropdown.value;
        if (!location || !level) return;

        // Clear dependent dropdown
        populateDropdown(boxDropdown, []);

        fetch("/box_maintenance/filter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ location, level }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Failed to fetch boxes: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                    return;
                }
                populateDropdown(boxDropdown, data.boxes || []);
            })
            .catch((error) => {
                console.error("Error filtering boxes:", error);
                alert("Failed to filter boxes. Please try again.");
            });
    });

    // Handle form submission
    boxForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const location = locationDropdown.value;
        const level = levelDropdown.value;
        const box = boxDropdown.value;

        if (!location || !level || !box) {
            alert("Please select location, level, and box.");
            return;
        }

        // Show loading indicator
        contentsContainer.innerHTML = '<p class="text-muted" aria-live="polite">Loading...</p>';

        // Disable submit button during fetch
        const submitButton = boxForm.querySelector("button[type='submit']");
        submitButton.disabled = true;

        fetch("/box_contents", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ location, level, box }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Failed to fetch box contents: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                submitButton.disabled = false; // Re-enable submit button
                contentsContainer.innerHTML = ""; // Clear loading message
                if (data.error) {
                    alert(data.error);
                    return;
                }

                if (data.length === 0) {
                    contentsContainer.innerHTML = '<p class="text-muted">No items found in this box.</p>';
                    return;
                }

                // Populate new contents
                console.log('Box contents received:', data);
                data.forEach((item) => {
                    console.log(`Part ${item.part_num}: image URL = "${item.image}"`);
                    const card = document.createElement("div");
                    card.className = "col-md-4 mb-3";
                    card.innerHTML = `
                        <div class="card h-100">
                            <img src="${item.image || '/static/default_image.png'}" class="card-img-top" alt="${item.name}" 
                                 onerror="console.error('Image failed to load:', this.src); this.src='/static/default_image.png'" 
                                 onload="console.log('Image loaded successfully:', this.src)"
                                 style="height: 200px; object-fit: contain;">
                            <div class="card-body">
                                <h5 class="card-title">${item.name}</h5>
                                <p class="card-text"><strong>Category:</strong> ${item.category}</p>
                                <p class="card-text"><strong>Part Number:</strong> ${item.part_num}</p>
                                <div class="form-check">
                                    <input class="form-check-input label-printed-checkbox" type="checkbox" 
                                           id="label-${item.storage_id}" data-storage-id="${item.storage_id}"
                                           ${item.label_printed ? 'checked' : ''}>
                                    <label class="form-check-label" for="label-${item.storage_id}">
                                        Label Printed
                                    </label>
                                </div>
                            </div>
                        </div>`;
                    contentsContainer.appendChild(card);
                });

                // Add event listeners for checkbox changes
                addLabelCheckboxListeners();
            })
            .catch((error) => {
                submitButton.disabled = false; // Re-enable submit button
                console.error("Error fetching box contents:", error);
                contentsContainer.innerHTML = '<p class="text-danger">Failed to load box contents.</p>';
            });
    });

    // Handle label generation
    labelButton.addEventListener("click", function () {
        const location = locationDropdown.value;
        const level = levelDropdown.value;
        const box = boxDropdown.value;

        if (!location || !level || !box) {
            alert("Please select location, level, and box.");
            return;
        }

        fetch("/box_maintenance/label", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ location, level, box }),
        })
            .then((response) => {
                if (!response.ok) {
                    return response.text().then((text) => {
                        throw new Error(`Error: ${text}`);
                    });
                }
                return response.blob();
            })
            .then((blob) => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${location}_${level}_${box}_label.jpg`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            })
            .catch((error) => {
                console.error("Error generating label:", error);
                alert(`Failed to generate label: ${error.message}`);
            });
        
    });

    // Function to add event listeners for label printed checkboxes
    function addLabelCheckboxListeners() {
        const checkboxes = document.querySelectorAll('.label-printed-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const storageId = this.getAttribute('data-storage-id');
                const isChecked = this.checked;
                
                // Update the database
                fetch('/box_maintenance/update_label_status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        storage_id: parseInt(storageId),
                        label_printed: isChecked
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Label status updated:', data);
                    // Optional: Show success feedback
                    // You could add a small toast notification here
                })
                .catch(error => {
                    console.error('Error updating label status:', error);
                    // Revert the checkbox state on error
                    this.checked = !isChecked;
                    alert('Failed to update label status. Please try again.');
                });
            });
        });
    }
});
