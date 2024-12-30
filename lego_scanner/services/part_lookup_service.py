"""
This module provides functions to load and save the master lookup data
from a JSON file used in the LEGO Scanner application.

It interacts with the file system to read and write JSON data, ensuring
that the operations occur within the Flask application context.
"""
from models import db, PartStorage


def load_part_lookup():
    """
    Load the master lookup data from the database.

    Returns:
        dict: The master lookup data loaded from the database.
    """
    lookup_data = {}
    lookup_entries = PartStorage.query.all()
    for entry in lookup_entries:
        lookup_data[entry.part_id] = {
            'location': entry.location,
            'level': entry.level,
            'box': entry.box
        }
    return lookup_data


def save_part_lookup(master_lookup):
    """
    Save the master lookup data to the database.

    Args:
        master_lookup (dict): The master lookup data to be saved.
    """
    for part_id, data in master_lookup.items():
        lookup_entry = PartStorage.query.filter_by(part_id=part_id).first()
        if lookup_entry:
            lookup_entry.location = data['location']
            lookup_entry.level = data['level']
            lookup_entry.box = data['box']
        else:
            new_entry = PartStorage(
                part_id=part_id,
                location=data['location'],
                level=data['level'],
                box=data['box']
            )
            db.session.add(new_entry)
    db.session.commit()
