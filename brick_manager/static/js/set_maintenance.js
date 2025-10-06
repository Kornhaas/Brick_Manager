document.addEventListener("DOMContentLoaded", function () {
    const setsTable = document.getElementById("sets-table");
    const setDetails = document.getElementById("set-details");
    const backToSetsButton = document.getElementById("back-to-sets");

    // Mark all parts as existing
    const markAllExistingButton =
      document.getElementById("mark-all-existing");

    markAllExistingButton.addEventListener("click", () => {
      // Get all input fields in the Non-Spare Parts and Spare Parts tables
      const partsTables = [
        document.getElementById("non-spare-parts-table-body"),
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

      filterRows(nonSparePartsRows);
      filterRows(sparePartsRows);
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

      resetFilter(nonSparePartsRows);
      resetFilter(sparePartsRows);
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
                        <td><img src="${part.part_img_url}" alt="${
                part.name
              }" class="img-thumbnail" width="50" style="cursor: pointer;" onclick="showImageModal('${part.part_img_url}', '${part.name} (${part.part_num})')" /></td>
                        <td>${part.part_num}</td>
                        <td>${part.name}</td>
                        <td>${part.category || "Unknown Category"}</td>
                        <td style="background-color: #${colorRgb}; color: ${textColor};">${part.color || "Not Specified"}</td>
                        <td>${part.quantity}</td>
                        <td>
                            <input type="number" name="part_id_${
                              part.id
                            }" value="${part.have_quantity}" min="0" max="${
                part.quantity
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
                                        <h6>Parts for ${minifig.name}:</h6>
                                        <table class="table table-sm table-striped">
                                            <thead>
                                                <tr>
                                                    <th>Image</th>
                                                    <th>Part Number</th>
                                                    <th>Name</th>
                                                    <th>Color</th>
                                                    <th>Quantity</th>
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