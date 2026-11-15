# pyright: reportCallIssue=false
"""

This module provides functions to load and save the master lookup data

from the `PartStorage` table used in the Brick Manager application.

It interacts with the database to query and update data, ensuring that the
operations occur within the Flask application context.
"""

from models import PartStorage, db

# Global cache for part lookup data to avoid reloading on every request
_part_lookup_cache = None  # pylint: disable=invalid-name
_cache_timestamp = None  # pylint: disable=invalid-name


def invalidate_part_lookup_cache():
    """Discard derived lookup data after a storage change."""
    global _part_lookup_cache, _cache_timestamp
    _part_lookup_cache = None
    _cache_timestamp = None


def load_part_lookup():
    """

    Load the master lookup data from the PartStorage table with caching.

    Cache is maintained across requests to avoid repeated database queries.

    Returns:
        dict: The master lookup data loaded from the database.
    """
    global _part_lookup_cache, _cache_timestamp

    import time

    current_time = time.time()

    # Use cache if it exists and is less than 5 minutes old
    if (
        _part_lookup_cache is not None
        and _cache_timestamp
        and (current_time - _cache_timestamp) < 300
    ):
        return _part_lookup_cache

    # Legacy readers receive a primary address only when it is unambiguous.
    # New readers consume the complete ID-based list, never a last-row-wins map.
    from services.storage_service import content_dict

    grouped = {}
    for entry in PartStorage.query.order_by(PartStorage.id).all():
        grouped.setdefault(entry.part_num, []).append(content_dict(entry))
    lookup_data = {}
    for part_num, entries in grouped.items():
        primary = entries[0] if len(entries) == 1 else {}
        lookup_data[part_num] = {
            "location": primary.get("location"),
            "level": primary.get("level"),
            "box": primary.get("box"),
            "locations": entries,
        }

    # Update cache
    _part_lookup_cache = lookup_data
    _cache_timestamp = current_time

    return lookup_data


def save_part_lookup(master_lookup):
    """

    Save the master lookup data to the PartStorage table and clear cache.


    Args:
        master_lookup (dict): The master lookup data to save.
    """
    global _part_lookup_cache, _cache_timestamp

    from services.storage_service import legacy_guard

    updates = []
    for part_num, data in master_lookup.items():
        # The dictionary may include untouched multi-location projections.
        if "locations" in data:
            originals = data["locations"]
            primary = originals[0] if len(originals) == 1 else {}
            if all(data.get(f) == primary.get(f) for f in ("location", "level", "box")):
                continue
        storage_entry = legacy_guard(part_num=part_num)
        updates.append((part_num, data, storage_entry))
    for part_num, data, storage_entry in updates:
        if storage_entry is None:
            storage_entry = PartStorage(part_num=part_num)
            db.session.add(storage_entry)
        for field in ("location", "level", "box"):
            if field in data:
                setattr(storage_entry, field, data[field])
        storage_entry.revision = (storage_entry.revision or 1) + 1
    db.session.commit()

    # Clear cache since data has been updated
    _part_lookup_cache = None
    _cache_timestamp = None


def search_parts(query, limit=10):
    """

    Search for parts based on a query string.


    Args:
        query (str): Search query
        limit (int): Maximum number of results to return

    Returns:
        list: List of matching parts
    """
    if not query:
        return []

    # Search in part numbers and locations
    results = (
        PartStorage.query.filter(PartStorage.part_num.like(f"%{query}%"))
        .limit(limit)
        .all()
    )

    return [
        {
            "part_num": result.part_num,
            "location": result.location,
            "level": result.level,
            "box": result.box,
        }
        for result in results
    ]
