import json

def load_master_lookup(filepath='lookup/master_lookup.json'):
    """Load the master lookup table from a JSON file."""
    with open(filepath, 'r') as file:
        return json.load(file)
