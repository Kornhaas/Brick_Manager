"""
This module handles the display of all missing parts and missing minifigure parts across all sets.
"""

import os
import re
import time
import urllib.parse
from urllib.parse import urlparse

from flask import Blueprint, current_app, jsonify, render_template, request, url_for
from models import (
    PartStorage,
    RebrickableColors,
    RebrickableInventories,
    RebrickableInventoryParts,
    RebrickablePartCategories,
    RebrickableParts,
    User_Parts,
    User_Set,
    UserMinifigurePart,
    db,
)
from services.cache_service import cache_image
from services.part_lookup_service import load_part_lookup

# pylint: disable=C0301
# Define a new Blueprint for missing parts
missing_parts_bp = Blueprint("missing_parts", __name__)

# In-memory cache for image URLs to avoid repeated filesystem checks
_image_url_cache = {}


def parse_internal_id_filter(id_filter):
    """
    Parse internal ID filter string and return a list of internal IDs to filter by.

    Supports formats:
    - Single ID: "229"
    - Range: "200-220"
    - List: "200;204;205" or "200,204,205"
    - Mixed: "200-210;229;250-260"

    Returns empty list if no filter or if filter is invalid.
    """
    if not id_filter or not id_filter.strip():
        return []

    internal_ids = []

    try:
        # Split by semicolon or comma
        parts = re.split("[;,]", id_filter.strip())

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if it's a range (contains dash)
            if "-" in part:
                try:
                    start, end = part.split("-", 1)
                    start_num = int(start.strip())
                    end_num = int(end.strip())
                    internal_ids.extend(str(i) for i in range(start_num, end_num + 1))
                except ValueError:
                    current_app.logger.warning(
                        f"Invalid range format in internal ID filter: {part}"
                    )
                    continue
            else:
                # Single internal ID
                try:
                    int(part)  # Validate it's a number
                    internal_ids.append(part)
                except ValueError:
                    current_app.logger.warning(f"Invalid internal ID in filter: {part}")
                    continue

        current_app.logger.info(
            f"Parsed internal ID filter '{id_filter}' to {len(internal_ids)} IDs: {internal_ids[:10]}{'...' if len(internal_ids) > 10 else ''}"
        )
        return internal_ids

    except Exception as e:
        current_app.logger.error(f"Error parsing internal ID filter '{id_filter}': {e}")
        return []


def should_include_set(user_set, allowed_internal_ids):
    """
    Check if a user set should be included based on the internal ID filter.

    Args:
        user_set: The user set object
        allowed_internal_ids: List of allowed internal IDs (empty means no filter)

    Returns:
        True if the set should be included, False otherwise
    """
    if not allowed_internal_ids:  # No filter applied
        return True

    # Filter by internal ID (user_set.id)
    internal_id_str = str(user_set.id)

    # Check for exact match first
    if internal_id_str in allowed_internal_ids:
        current_app.logger.debug(
            f"Including user set {user_set.id} (internal ID match)"
        )
        return True

    # Check if the internal ID starts with any of the allowed numbers (for range support)
    for allowed_id in allowed_internal_ids:
        if internal_id_str.startswith(allowed_id) and (
            len(internal_id_str) == len(allowed_id)
            or not internal_id_str[len(allowed_id)].isdigit()
        ):
            current_app.logger.debug(
                f"Including user set {user_set.id} (partial internal ID match with {allowed_id})"
            )
            return True

    return False


def get_cached_image_url(image_url):
    """
    Optimized image URL getter that avoids repeated filesystem checks.
    Uses in-memory cache to remember which images are already cached.
    """
    if not image_url:
        return "/static/default_image.png"

    # Check memory cache first
    if image_url in _image_url_cache:
        return _image_url_cache[image_url]

    try:
        # Quick filesystem check for cached file
        raw_filename = os.path.basename(urlparse(image_url).path)
        if not raw_filename:
            _image_url_cache[image_url] = "/static/default_image.png"
            return "/static/default_image.png"

        cache_dir = "/workspaces/Bricks_Manager/brick_manager/static/cache/images"
        cached_path = os.path.join(cache_dir, raw_filename)

        if os.path.exists(cached_path):
            # File is cached, return the static URL
            cached_url = f"/static/cache/images/{raw_filename}"
            _image_url_cache[image_url] = cached_url
            return cached_url
        else:
            # File not cached - return original URL to avoid synchronous download delay
            # Images will be cached lazily when first accessed by the browser
            _image_url_cache[image_url] = image_url
            return image_url

    except Exception as e:
        current_app.logger.warning(f"Error checking cached image {image_url}: {e}")
        fallback = "/static/default_image.png"
        _image_url_cache[image_url] = fallback
        return fallback


def bulk_enrich_missing_parts(parts_list, master_lookup):
    """Bulk enrich multiple parts with single database queries instead of N individual queries"""
    if not parts_list:
        return []

    current_app.logger.info(f"Bulk enriching {len(parts_list)} parts")

    # Extract all unique part numbers and color IDs
    part_nums = list(set(part[0].part_num for part in parts_list))
    color_ids = list(set(part[0].color_id for part in parts_list))

    # Bulk query 1: Get all part storage data
    storage_data = {}
    if part_nums:
        storage_query = (
            db.session.query(PartStorage)
            .filter(PartStorage.part_num.in_(part_nums))
            .all()
        )
        storage_data = {s.part_num: s for s in storage_query}

    # Bulk query 2: Get all part info and colors with single JOIN
    part_color_data = {}
    if part_nums:
        part_color_query = (
            db.session.query(RebrickableParts)
            .filter(RebrickableParts.part_num.in_(part_nums))
            .all()
        )

        for part_info in part_color_query:
            part_color_data[part_info.part_num] = (part_info, None)

    # Bulk query 3: Get all color information
    colors_data = {}
    if color_ids:
        colors_query = (
            db.session.query(RebrickableColors)
            .filter(RebrickableColors.id.in_(color_ids))
            .all()
        )
        colors_data = {c.id: c for c in colors_query}

    # Bulk query 4: Get inventory images for all parts
    inventory_images = {}
    if part_nums:
        inv_query = (
            db.session.query(
                RebrickableInventoryParts.part_num,
                RebrickableInventoryParts.color_id,
                RebrickableInventoryParts.img_url,
            )
            .filter(
                RebrickableInventoryParts.part_num.in_(part_nums),
                RebrickableInventoryParts.img_url.isnot(None),
                RebrickableInventoryParts.img_url != "",
            )
            .all()
        )

        for part_num, color_id, img_url in inv_query:
            key = f"{part_num}_{color_id}"
            if key not in inventory_images:  # Use first found image
                inventory_images[key] = img_url

    # Process each part using bulk-loaded data
    enriched_parts = []
    for part_obj, user_set, part_type in parts_list:
        try:
            # Use bulk-loaded data instead of individual queries
            storage = storage_data.get(part_obj.part_num)
            part_info, _ = part_color_data.get(part_obj.part_num, (None, None))
            color_info = colors_data.get(part_obj.color_id)

            # Get inventory image
            inv_key = f"{part_obj.part_num}_{part_obj.color_id}"
            inventory_img_url = inventory_images.get(inv_key)

            # Determine best image URL
            best_img_url = inventory_img_url or (
                part_info.part_img_url if part_info else None
            )

            if (
                best_img_url
                and best_img_url.strip()
                and best_img_url.strip().lower() != "none"
            ):
                cached_img_url = get_cached_image_url(best_img_url)
            else:
                cached_img_url = "/static/default_image.png"

            # Get location data
            part_data = master_lookup.get(part_obj.part_num, {})
            location_data = (
                f"Location: {part_data.get('location', 'Unknown')}, "
                f"Level: {part_data.get('level', 'Unknown')}, "
                f"Box: {part_data.get('box', 'Unknown')}"
                if part_data
                else "Not Specified"
            )

            result = {
                "type": part_type,
                "set_id": user_set.template_set.set_num
                if user_set.template_set
                else "Unknown",
                "internal_id": user_set.id,
                "item_id": part_obj.part_num,
                "name": part_info.name if part_info else "Unknown",
                "category": part_info.category.name
                if part_info and hasattr(part_info, "category") and part_info.category
                else "Unknown Category",
                "color": color_info.name if color_info else "Unknown",
                "color_rgb": color_info.rgb if color_info else "FFFFFF",
                "color_id": part_obj.color_id,
                "is_spare": part_obj.is_spare,
                "missing_quantity": part_obj.quantity - part_obj.have_quantity,
                "have_quantity": part_obj.have_quantity,
                "total_quantity": part_obj.quantity,
                "img_url": cached_img_url,
                "location": location_data,
                "status": "Available" if storage else "Not Available",
            }

            enriched_parts.append(result)

        except Exception as e:
            current_app.logger.error(
                f"Error bulk enriching {part_type.lower()} {part_obj.part_num}: {str(e)}"
            )
            continue

    current_app.logger.info(f"Successfully bulk enriched {len(enriched_parts)} parts")
    return enriched_parts


def enrich_missing_part(part, user_set, part_type="Regular Part"):
    """Helper function to enrich part data with proper images and color information"""
    try:
        current_app.logger.debug(
            f"Enriching {part_type} part: {part.part_num} for set {user_set.id}"
        )

        storage_data = (
            db.session.query(PartStorage).filter_by(part_num=part.part_num).first()
        )
        current_app.logger.debug(
            f"Storage data found for {part.part_num}: {storage_data is not None}"
        )

        # Get part info with proper joins to get color and image information
        part_query = (
            db.session.query(RebrickableParts, RebrickableColors)
            .join(RebrickableColors, RebrickableColors.id == part.color_id)
            .filter(RebrickableParts.part_num == part.part_num)
            .first()
        )

        part_info = part_query[0] if part_query else None
        color_info = part_query[1] if part_query else None

        # Try to get inventory-specific image URL
        inventory_img_url = None
        if user_set.template_set:
            inventory = RebrickableInventories.query.filter_by(
                set_num=user_set.template_set.set_num
            ).first()
            if inventory:
                # First try: exact color match in this set
                inv_part = RebrickableInventoryParts.query.filter_by(
                    inventory_id=inventory.id,
                    part_num=part.part_num,
                    color_id=part.color_id,
                ).first()
                if inv_part and inv_part.img_url:
                    inventory_img_url = inv_part.img_url

        # If no set-specific image found, try to get ANY inventory image for this part
        if not inventory_img_url:
            fallback_inv_part = RebrickableInventoryParts.query.filter(
                RebrickableInventoryParts.part_num == part.part_num,
                RebrickableInventoryParts.img_url.isnot(None),
                RebrickableInventoryParts.img_url != "",
            ).first()
            if fallback_inv_part and fallback_inv_part.img_url:
                inventory_img_url = fallback_inv_part.img_url

        # Determine the best image URL (inventory-specific first, then generic part image)
        best_img_url = inventory_img_url or (
            part_info.part_img_url if part_info else None
        )

        # Handle various "empty" cases: None, empty string, or literal 'None' string
        if (
            best_img_url
            and best_img_url.strip()
            and best_img_url.strip().lower() != "none"
        ):
            # Optimize: Try to return cached image directly without re-processing
            cached_img_url = get_cached_image_url(best_img_url)
        else:
            cached_img_url = "/static/default_image.png"

        master_lookup = load_part_lookup()
        part_data = master_lookup.get(part.part_num, {})
        location_data = (
            f"Location: {part_data.get('location', 'Unknown')}, "
            f"Level: {part_data.get('level', 'Unknown')}, "
            f"Box: {part_data.get('box', 'Unknown')}"
            if part_data
            else "Not Specified"
        )

        result = {
            "type": part_type,
            "set_id": user_set.template_set.set_num
            if user_set.template_set
            else "Unknown",
            "internal_id": user_set.id,
            "item_id": part.part_num,
            "name": part_info.name if part_info else "Unknown",
            "category": part_info.category.name
            if part_info and hasattr(part_info, "category") and part_info.category
            else "Unknown Category",
            "color": color_info.name if color_info else "Unknown",
            "color_rgb": color_info.rgb if color_info else "FFFFFF",
            "color_id": part.color_id,
            "is_spare": part.is_spare,
            "missing_quantity": part.quantity - part.have_quantity,
            "have_quantity": part.have_quantity,
            "total_quantity": part.quantity,
            "img_url": cached_img_url,
            "location": location_data,
            "status": "Available" if storage_data else "Not Available",
        }

        return result

    except Exception as e:
        current_app.logger.error(f"Error enriching part {part.part_num}: {str(e)}")
        # Return a basic result to prevent crashes
        return {
            "type": part_type,
            "set_id": user_set.template_set.set_num
            if hasattr(user_set, "template_set") and user_set.template_set
            else "Unknown",
            "internal_id": user_set.id,
            "item_id": part.part_num,
            "name": "Unknown",
            "category": "Unknown Category",
            "color": "Unknown",
            "color_rgb": "FFFFFF",
            "color_id": getattr(part, "color_id", None),
            "is_spare": getattr(part, "is_spare", False),
            "missing_quantity": part.quantity - part.have_quantity,
            "have_quantity": getattr(part, "have_quantity", 0),
            "total_quantity": getattr(part, "quantity", 0),
            "img_url": "/static/default_image.png",
            "location": "Not Specified",
            "status": "Not Available",
        }


def get_missing_parts_categories(include_spare=True, set_filter=""):
    """Get summary of missing parts grouped by category with total statistics"""
    start_time = time.time()
    current_app.logger.info("Starting category summary analysis")

    # Parse internal ID filter
    allowed_internal_ids = parse_internal_id_filter(set_filter)
    if allowed_internal_ids:
        current_app.logger.info(
            f"Filtering by {len(allowed_internal_ids)} internal IDs"
        )

    categories = {}

    # Initialize counters for statistics
    total_missing_parts = 0
    total_missing_spare_parts = 0
    total_missing_regular_parts = 0

    try:
        # Query all User_Sets to get missing regular parts by category
        query_start = time.time()
        user_sets = User_Set.query.all()
        query_time = time.time() - query_start
        current_app.logger.info(
            f"Queried {len(user_sets)} user sets in {query_time:.2f} seconds"
        )

        # Process regular parts
        regular_start = time.time()
        filtered_sets_count = 0
        total_sets_checked = 0

        for user_set in user_sets:
            total_sets_checked += 1

            # Apply internal ID filter
            if not should_include_set(user_set, allowed_internal_ids):
                continue

            filtered_sets_count += 1

            if not hasattr(user_set, "parts_in_set") or user_set.parts_in_set is None:
                continue

            parts_in_set_count = (
                len(user_set.parts_in_set) if user_set.parts_in_set else 0
            )
            missing_parts_count = 0

            for part in user_set.parts_in_set:
                if part.quantity > part.have_quantity:
                    missing_parts_count += 1
                    missing_quantity = part.quantity - part.have_quantity

                    # Track statistics for all missing parts
                    is_spare = getattr(part, "is_spare", False)
                    if is_spare:
                        total_missing_spare_parts += missing_quantity
                    else:
                        total_missing_regular_parts += missing_quantity
                    total_missing_parts += missing_quantity

                    # Skip spare parts if not requested
                    if not include_spare and is_spare:
                        continue

                    # Get category information efficiently
                    part_info = (
                        db.session.query(RebrickableParts)
                        .filter_by(part_num=part.part_num)
                        .first()
                    )
                    if part_info and part_info.category:
                        category_name = part_info.category.name
                    else:
                        category_name = "Unknown Category"

                    if category_name not in categories:
                        categories[category_name] = {"count": 0, "total_missing": 0}

                    categories[category_name]["count"] += 1
                    categories[category_name]["total_missing"] += (
                        part.quantity - part.have_quantity
                    )

            if filtered_sets_count <= 5:  # Log details for first few sets
                set_num = (
                    user_set.template_set.set_num if user_set.template_set else "None"
                )
                current_app.logger.debug(
                    f"Processed set {user_set.id} (set_num: {set_num}) - {parts_in_set_count} total parts, {missing_parts_count} missing parts"
                )

        current_app.logger.info(
            f"Checked {total_sets_checked} user sets, {filtered_sets_count} matched filter"
        )
        regular_time = time.time() - regular_start
        current_app.logger.info(
            f"Processed regular parts in {regular_time:.2f} seconds"
        )

        # Process minifigure parts
        minifig_start = time.time()
        user_minifigure_parts = UserMinifigurePart.query.all()

        for minifig_part in user_minifigure_parts:
            # Apply internal ID filter for minifigure parts
            if hasattr(minifig_part, "user_set") and minifig_part.user_set:
                if not should_include_set(minifig_part.user_set, allowed_internal_ids):
                    continue

            if minifig_part.quantity > minifig_part.have_quantity:
                missing_quantity = minifig_part.quantity - minifig_part.have_quantity

                # Track statistics for minifigure parts (usually not spare parts)
                is_spare = getattr(minifig_part, "is_spare", False)
                if is_spare:
                    total_missing_spare_parts += missing_quantity
                else:
                    total_missing_regular_parts += missing_quantity
                total_missing_parts += missing_quantity

                # Skip spare parts if not requested
                if not include_spare and is_spare:
                    continue

                # Get category information efficiently
                part_info = (
                    db.session.query(RebrickableParts)
                    .filter_by(part_num=minifig_part.part_num)
                    .first()
                )
                if part_info and part_info.category:
                    category_name = part_info.category.name
                else:
                    category_name = "Unknown Category"

                if category_name not in categories:
                    categories[category_name] = {"count": 0, "total_missing": 0}

                categories[category_name]["count"] += 1
                categories[category_name]["total_missing"] += (
                    minifig_part.quantity - minifig_part.have_quantity
                )

        minifig_time = time.time() - minifig_start
        current_app.logger.info(
            f"Processed minifigure parts in {minifig_time:.2f} seconds"
        )

        # Convert to sorted list
        category_list = [
            {
                "name": name,
                "count": data["count"],
                "total_missing": data["total_missing"],
            }
            for name, data in categories.items()
        ]
        category_list.sort(key=lambda x: x["name"])

        total_time = time.time() - start_time
        current_app.logger.info(
            f"Category summary complete in {total_time:.2f} seconds. Found {len(category_list)} categories"
        )

        # Log statistics
        current_app.logger.info(
            f"Missing parts statistics - Total: {total_missing_parts}, Regular: {total_missing_regular_parts}, Spare: {total_missing_spare_parts}"
        )

        return {
            "categories": category_list,
            "statistics": {
                "total_missing_parts": total_missing_parts,
                "total_missing_regular_parts": total_missing_regular_parts,
                "total_missing_spare_parts": total_missing_spare_parts,
                "total_sets_checked": total_sets_checked,
                "filtered_sets_count": filtered_sets_count,
                "has_filter": bool(allowed_internal_ids),
            },
        }

    except Exception as e:
        current_app.logger.error(f"Error in get_missing_parts_categories: {str(e)}")
        current_app.logger.exception("Full traceback:")
        return {
            "categories": [],
            "statistics": {
                "total_missing_parts": 0,
                "total_missing_regular_parts": 0,
                "total_missing_spare_parts": 0,
                "total_sets_checked": 0,
                "filtered_sets_count": 0,
                "has_filter": False,
            },
        }


@missing_parts_bp.route("/missing_parts_category/<path:category_name>", methods=["GET"])
def missing_parts_category(category_name):
    """Get missing parts for a specific category"""
    start_time = time.time()

    # URL decode the category name to handle special characters
    decoded_category_name = urllib.parse.unquote(category_name)
    current_app.logger.info(
        f"Getting missing parts for category: '{decoded_category_name}' (original: '{category_name}')"
    )

    missing_items = []
    include_spare = request.args.get("include_spare", "true").lower() == "true"
    set_filter = request.args.get("set_filter", "").strip()

    # Parse internal ID filter
    allowed_internal_ids = parse_internal_id_filter(set_filter)
    if allowed_internal_ids:
        current_app.logger.info(
            f"Filtering category parts by {len(allowed_internal_ids)} internal IDs"
        )

    try:
        # Step 1: Collect all parts that need checking (without individual DB queries)
        parts_to_check = []

        # Collect regular parts
        user_sets = User_Set.query.all()
        for user_set in user_sets:
            # Apply internal ID filter
            if not should_include_set(user_set, allowed_internal_ids):
                continue

            if not hasattr(user_set, "parts_in_set") or user_set.parts_in_set is None:
                continue
            for part in user_set.parts_in_set:
                if part.quantity > part.have_quantity:
                    if not include_spare and part.is_spare:
                        continue
                    parts_to_check.append(
                        (part.part_num, part, user_set, "Regular Part")
                    )

        # Collect minifigure parts
        user_minifigure_parts = UserMinifigurePart.query.all()
        for minifig_part in user_minifigure_parts:
            # Apply internal ID filter for minifigure parts
            if hasattr(minifig_part, "user_set") and minifig_part.user_set:
                if not should_include_set(minifig_part.user_set, allowed_internal_ids):
                    continue

            if minifig_part.quantity > minifig_part.have_quantity:
                if not include_spare and minifig_part.is_spare:
                    continue
                parts_to_check.append(
                    (
                        minifig_part.part_num,
                        minifig_part,
                        minifig_part.user_set,
                        "Minifigure Part",
                    )
                )

        # Step 2: BULK query for all part categories (single DB query instead of N queries)
        all_part_nums = list(set(item[0] for item in parts_to_check))
        part_categories = {}

        if all_part_nums:
            current_app.logger.info(
                f"Bulk querying categories for {len(all_part_nums)} unique parts"
            )
            category_query = (
                db.session.query(
                    RebrickableParts.part_num, RebrickablePartCategories.name
                )
                .join(
                    RebrickablePartCategories,
                    RebrickableParts.part_cat_id == RebrickablePartCategories.id,
                )
                .filter(RebrickableParts.part_num.in_(all_part_nums))
                .all()
            )

            part_categories = {row[0]: row[1] for row in category_query}
            current_app.logger.info(
                f"Found categories for {len(part_categories)} parts"
            )

        # Step 3: Filter parts in the target category
        category_parts = []
        for part_num, part_obj, user_set, part_type in parts_to_check:
            part_category = part_categories.get(part_num, "Unknown Category")

            if part_category == decoded_category_name:
                category_parts.append((part_obj, user_set, part_type))

        # Step 4: Bulk enrich all parts in this category (single DB queries instead of N queries)
        if category_parts:
            # Load part lookup data once for all parts (instead of loading it inside bulk_enrich_missing_parts)
            master_lookup = load_part_lookup()
            missing_items = bulk_enrich_missing_parts(category_parts, master_lookup)

        # Sort by Color, Part Name, Internal ID
        missing_items.sort(key=lambda x: (x["color"], x["name"], x["internal_id"]))

        total_time = time.time() - start_time
        current_app.logger.info(
            f"Retrieved {len(missing_items)} missing parts for category '{decoded_category_name}' in {total_time:.2f} seconds"
        )

        return jsonify(missing_items)

    except Exception as e:
        current_app.logger.error(f"Error in missing_parts_category route: {str(e)}")
        current_app.logger.exception("Full traceback:")
        return jsonify([])


@missing_parts_bp.route("/missing_parts", methods=["GET"])
def missing_parts():
    """
    Displays category summary for missing parts and missing minifigure parts across all sets.
    """
    start_time = time.time()
    current_app.logger.info("Starting missing parts category analysis")

    try:
        # Get spare parts parameter from query string
        include_spare = request.args.get("include_spare", "true").lower() == "true"

        # Get set filtering parameters
        set_filter = request.args.get("set_filter", "").strip()

        result = get_missing_parts_categories(
            include_spare=include_spare, set_filter=set_filter
        )

        categories = result["categories"]
        statistics = result["statistics"]

        total_time = time.time() - start_time
        current_app.logger.info(
            f"Missing parts category analysis complete in {total_time:.2f} seconds"
        )

        return render_template(
            "missing_parts.html",
            categories=categories,
            statistics=statistics,
            include_spare=include_spare,
            set_filter=set_filter,
        )

    except Exception as e:
        current_app.logger.error(f"Error in missing_parts route: {str(e)}")
        current_app.logger.exception("Full traceback:")
        # Return empty categories and statistics to prevent crash
        empty_statistics = {
            "total_missing_parts": 0,
            "total_missing_regular_parts": 0,
            "total_missing_spare_parts": 0,
            "total_sets_checked": 0,
            "filtered_sets_count": 0,
            "has_filter": False,
        }
        return render_template(
            "missing_parts.html",
            categories=[],
            statistics=empty_statistics,
            include_spare=True,
            set_filter="",
        )


@missing_parts_bp.route("/missing_parts_categories", methods=["GET"])
def missing_parts_categories_api():
    """
    API endpoint to get category summary with spare parts filtering.
    """
    try:
        include_spare = request.args.get("include_spare", "true").lower() == "true"
        set_filter = request.args.get("set_filter", "").strip()
        result = get_missing_parts_categories(
            include_spare=include_spare, set_filter=set_filter
        )
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(
            f"Error in missing_parts_categories_api route: {str(e)}"
        )
        return jsonify(
            {
                "categories": [],
                "statistics": {
                    "total_missing_parts": 0,
                    "total_missing_regular_parts": 0,
                    "total_missing_spare_parts": 0,
                    "total_sets_checked": 0,
                    "filtered_sets_count": 0,
                    "has_filter": False,
                },
            }
        )


@missing_parts_bp.route("/update_part_quantity", methods=["POST"])
def update_part_quantity():
    """Update the have_quantity for a specific part"""
    try:
        data = request.get_json()
        part_id = data.get("part_id")
        set_id = int(data.get("set_id"))
        part_type = data.get("part_type")
        is_spare = data.get("is_spare", False)
        color_id = data.get("color_id")
        new_quantity = int(data.get("have_quantity"))

        current_app.logger.info(
            f"Updating {part_type} quantity: part={part_id}, set={set_id}, spare={is_spare}, color={color_id}, quantity={new_quantity}"
        )

        if part_type == "Regular Part":
            # Update regular part with more specific filtering
            query = User_Parts.query.filter_by(
                part_num=part_id, user_set_id=set_id, is_spare=is_spare
            )

            # Add color_id filter if provided
            if color_id:
                query = query.filter_by(color_id=int(color_id))

            part = query.first()

            if not part:
                current_app.logger.error(
                    f"Regular part not found: part_num={part_id}, user_set_id={set_id}, is_spare={is_spare}, color_id={color_id}"
                )
                return jsonify({"success": False, "message": "Part not found"}), 404

            part.have_quantity = new_quantity

        elif part_type == "Minifigure Part":
            # Update minifigure part with more specific filtering
            query = UserMinifigurePart.query.filter_by(
                part_num=part_id, user_set_id=set_id, is_spare=is_spare
            )

            # Add color_id filter if provided
            if color_id:
                query = query.filter_by(color_id=int(color_id))

            part = query.first()

            if not part:
                current_app.logger.error(
                    f"Minifigure part not found: part_num={part_id}, user_set_id={set_id}, is_spare={is_spare}, color_id={color_id}"
                )
                return (
                    jsonify({"success": False, "message": "Minifigure part not found"}),
                    404,
                )

            part.have_quantity = new_quantity

        else:
            return jsonify({"success": False, "message": "Invalid part type"}), 400

        # Commit the changes
        db.session.commit()

        current_app.logger.info(
            f"Successfully updated {part_type} quantity for {part_id} in set {set_id} (spare: {is_spare})"
        )

        return jsonify(
            {
                "success": True,
                "message": "Quantity updated successfully",
                "total_quantity": part.quantity,
                "have_quantity": part.have_quantity,
                "missing_quantity": part.quantity - part.have_quantity,
            }
        )

    except ValueError as e:
        current_app.logger.error(f"Invalid data types in request: {str(e)}")
        return jsonify({"success": False, "message": "Invalid data format"}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating part quantity: {str(e)}")
        current_app.logger.exception("Full traceback:")
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
