import json
import os

def load_master_lookup(file_path='master_lookup.json'):
    """Load the master lookup table from a JSON file."""
    if not os.path.exists(file_path):
        print(f"Lookup file {file_path} does not exist.")
        return {}

    with open(file_path, 'r') as f:
        try:
            lookup_table = json.load(f)
            print(f"Loaded lookup table from {file_path}")
            return lookup_table
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {file_path}")
            return {}
