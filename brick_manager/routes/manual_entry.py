"""
This module handles the manual entry of Brick parts into the master lookup.
Users can manually enter part details such as part ID, location (schrank), level (fach), and box.
The data is either added to or updated in the master lookup.
"""

from flask import Blueprint, flash, render_template, request
from services.part_lookup_service import load_part_lookup, save_part_lookup

# pylint: disable=W0718

manual_entry_bp = Blueprint("manual_entry", __name__)


@manual_entry_bp.route("/manual_entry", methods=["GET", "POST"])
def manual_entry():
    """
    Handles manual entry of part information. If the part ID already exists in the master lookup,
    it shows a confirmation dialog before overwriting the entry.
    """
    try:
        master_lookup = load_part_lookup()
    except Exception as error:
        flash(f"Error loading master lookup: {error}", "danger")
        return render_template("manual_entry.html", existing_entry=None)

    if request.method == "POST":
        part_num = request.form.get("part_num")
        schrank = request.form.get("schrank")
        fach = request.form.get("fach")
        box = request.form.get("box")
        confirmed = request.form.get("confirmed")  # Track confirmation

        # Validate inputs
        if not part_num or not part_num.strip():
            flash("Part ID cannot be empty.", "danger")
        elif not all(val.isdigit() for val in [schrank, fach, box]):
            flash("Location, Level, and Box must be numeric.", "danger")
        else:
            # Check if part ID exists
            existing_entry = master_lookup.get(part_num)
            if existing_entry and not confirmed:
                flash(
                    f"Part Number {part_num} already exists. Confirm overwrite.",
                    "warning",
                )
                return render_template(
                    "manual_entry.html",
                    part_num=part_num,
                    schrank=schrank,
                    fach=fach,
                    box=box,
                    existing_entry=existing_entry,
                )

            # Add or update entry in the master lookup
            master_lookup[part_num] = {"location": schrank, "level": fach, "box": box}
            action = "updated" if existing_entry else "added"
            flash(f"Part Number {part_num} successfully {action}.", "success")

            # Save changes
            try:
                save_part_lookup(master_lookup)
            except Exception as save_error:
                flash(f"Error saving master lookup: {save_error}", "danger")
                return render_template("manual_entry.html", existing_entry=None)

            # Prepare for next entry with incremented box number
            next_box = str(int(box) + 1)
            return render_template(
                "manual_entry.html",
                part_num="",
                schrank=schrank,
                fach=fach,
                box=next_box,
                existing_entry=None,
            )

    return render_template("manual_entry.html", existing_entry=None)
