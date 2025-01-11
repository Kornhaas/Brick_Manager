"""
This module provides functions to load and save the master lookup data
from the `PartStorage` table used in the Brick Manager application.

It interacts with the database to query and update data, ensuring that the
operations occur within the Flask application context.
"""
from models import db, PartStorage


def load_part_lookup():
    """
    Load the master lookup data from the PartStorage table.

    Returns:
        dict: The master lookup data loaded from the database.
    """
    lookup_data = {}
    lookup_entries = PartStorage.query.all()
    for entry in lookup_entries:
        lookup_data[entry.part_num] = {
            'location': entry.location,
            'level': entry.level,
            'box': entry.box,
        }
    return lookup_data


def save_part_lookup(master_lookup):
    """
    Save the master lookup data to the PartStorage table.

    Args:
        master_lookup (dict): The master lookup data to be saved.
    """
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
