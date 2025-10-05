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
            const quantityCell = row.querySelector("td:nth-child(4)"); // Quantity cell
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
          const quantityCell = row.querySelector("td:nth-child(4)");
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
        const userSetId = button.getAttribute("data-user-set-id");
        fetch(`/set_maintain/${userSetId}`)
          .then((response) => response.json())
          .then((data) => {
            setDetails.classList.remove("hidden");
            setsTable.classList.add("hidden");
            document.getElementById("user-set-id").value = userSetId;

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
              const mismatchClass =
                part.quantity !== part.have_quantity ? "table-warning" : "";
              const partRow = `
                    <tr class="${mismatchClass}">
                        <td><img src="${part.part_img_url}" alt="${
                part.name
              }" width="50"></td>
                        <td>${part.name}</td>
                        <td>${part.color || "Not Specified"}</td>
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

            // Populate Minifigures Table
            const minifigsTableBody = document.getElementById(
              "minifigs-table-body"
            );
            minifigsTableBody.innerHTML = "";
            data.minifigs.forEach((minifig) => {
              minifigsTableBody.innerHTML += `
                                <tr>
                                    <td><img src="${minifig.img_url}" alt="${minifig.name}" width="50"></td>
                                    <td>${minifig.name}</td>
                                    <td>${minifig.quantity}</td>
                                </tr>`;
            });

            // Populate Minifigure Parts Table
            const minifigPartsTableBody = document.getElementById(
              "minifig-parts-table-body"
            );
            minifigPartsTableBody.innerHTML = "";
            data.minifigure_parts.forEach((part) => {
              const mismatchClass =
                part.quantity !== part.have_quantity ? "table-warning" : "";
              minifigPartsTableBody.innerHTML += `
                                <tr class="${mismatchClass}">
                                    <td><img src="${
                                      part.part_img_url
                                    }" alt="${part.name}" width="50"></td>
                                    <td>${part.part_num}</td>
                                    <td>${part.name}</td>
                                    <td>${part.quantity}</td>
                                    <td>
                                        <input type="number" name="minifig_part_id_${
                                          part.id
                                        }" value="${
                part.have_quantity
              }" min="0" max="${part.quantity}" class="form-control">
                                    </td>
                                    <td>${
                                      part.location || "Not Specified"
                                    }</td>
                                </tr>`;
            });

            document.getElementById("status").value = data.status;
          })
          .catch((error) =>
            console.error("Error fetching UserSet details:", error)
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
        const userSetId = button.getAttribute("data-user-set-id");
        const boxSize = button.getAttribute("data-box-size");

        fetch("/set_maintain/generate_label", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ set_id: userSetId, box_size: boxSize }),
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
            a.download = `${userSetId}_${boxSize}.drawio`;
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