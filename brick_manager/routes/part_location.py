import logging
from flask import Blueprint, render_template, request, jsonify
from services.rebrickable_service import RebrickableService
from services.part_lookup_service import load_part_lookup, save_part_lookup
# Import the centralized cache_image function
from services.cache_service import cache_image
from services.label_service import create_label_image

part_location_bp = Blueprint('part_location', __name__)


@part_location_bp.route('/part_location', methods=['GET', 'POST'])
def part_location():
    """
    Page to manage part locations. Fetches categories and allows the user to input locations.
    """
    categories = RebrickableService.get_all_category_ids()
    # Alphabetically sort categories
    categories.sort(key=lambda category: category[1])
    master_lookup = load_part_lookup()

    if request.method == 'POST':
        selected_category_id = request.form.get('category_id')
        page = int(request.form.get('page', 1))
        # Preserve card state from POST data
        card_state = request.form.get('card_state', 'expanded')

        try:
            logging.debug(f"Fetching parts for category {
                          selected_category_id}, page {page}")
            logging.debug(f"Categories: {categories}")
            selected_category_name = next(
                (category[1] for category in categories if category[0]
                 == int(selected_category_id)),
                None
            )
            parts_data = RebrickableService.get_parts_by_category(
                selected_category_id, page_size=5000, page=page)
            parts = parts_data.get('results', [])

            # Enrich parts with master lookup and cached images
            for part in parts:
                part_num = part['part_num']
                part['category'] = next(
                    (cat[1] for cat in categories if cat[0]
                     == part.get('part_cat_id')), "Unknown"
                )
                part_info = master_lookup.get(part_num, {})
                part['location'] = part_info.get('location', '')
                part['level'] = part_info.get('level', '')
                part['box'] = part_info.get('box', '')
                part['cached_img_url'] = cache_image(
                    part['part_img_url'] or "/static/default_image.png")

            pagination = {
                'count': parts_data.get('count', 0),
                'next': parts_data.get('next'),
                'previous': parts_data.get('previous')
            }
        except Exception as e:
            logging.error(f"Error fetching parts: {e}")
            return render_template('error.html', message=str(e))

        return render_template(
            'part_location.html',
            categories=categories,
            selected_category_name=selected_category_name,
            selected_category_id=selected_category_id,
            card_state=card_state,  # Pass card state
            parts=parts,
            pagination=pagination,
            page=page
        )

    # First load defaults card state to "expanded"
    return render_template('part_location.html', categories=categories, parts=[], card_state="expanded")


@part_location_bp.route('/save_locations', methods=['POST'])
def save_locations():
    """
    Save part location data (location, level, box) to the master lookup.
    """
    try:
        locations_data = request.json  # Expecting a JSON payload with part locations
        master_lookup = load_part_lookup()  # Load current master lookup

        # Update the master lookup with new location data
        for part_num, location_data in locations_data.items():
            if part_num not in master_lookup:
                master_lookup[part_num] = {}
            master_lookup[part_num].update(location_data)

        save_part_lookup(master_lookup)  # Save updated master lookup
        return jsonify({"message": "Locations saved successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@part_location_bp.route('/create_label', methods=['POST'])
def create_label():
    """
    Create a label for the specified part.
    """
    try:
        label_data = request.json  # Expecting label details in JSON format
        label_image_path = create_label_image(label_data)
        return jsonify({"success": True, "image_path": label_image_path}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
