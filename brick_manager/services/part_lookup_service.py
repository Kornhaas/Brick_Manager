"""
This module provides functions to load and save the master lookup data
from the `PartStorage` table used in the Brick Manager application.

It interacts with the database to query and update data, ensuring that the
operations occur within the Flask application context.
"""
from models import db, PartStorage

# Global cache for part lookup data to avoid reloading on every request
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
    if _part_lookup_cache is not None and _cache_timestamp and (current_time - _cache_timestamp) < 300:
        return _part_lookup_cache
    
    # Load from database and cache the result
    lookup_data = {}
    lookup_entries = PartStorage.query.all()
    for entry in lookup_entries:
        lookup_data[entry.part_num] = {
            'location': entry.location,
            'level': entry.level,
            'box': entry.box,
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
    
    for part_num, data in master_lookup.items():
        # Retrieve or create an entry in PartStorage
        storage_entry = PartStorage.query.filter_by(part_num=part_num).first()

        if storage_entry:
            # Update the existing entry
            storage_entry.location = data.get(
                'location', storage_entry.location)
            storage_entry.level = data.get('level', storage_entry.level)
            storage_entry.box = data.get('box', storage_entry.box)
        else:
            # Create a new entry
            new_entry = PartStorage(
                part_num=part_num,
                location=data.get('location', ''),
                level=data.get('level', ''),
                box=data.get('box', ''),
            )
            db.session.add(new_entry)

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
    from models import PartStorage
    
    if not query:
        return []
    
    # Search in part numbers and locations
    results = PartStorage.query.filter(
        PartStorage.part_num.like(f'%{query}%')
    ).limit(limit).all()
    
    return [{'part_num': result.part_num, 'location': result.location, 
             'level': result.level, 'box': result.box} for result in results]
