"""
Migration script to add color_id and notes fields to part_storage table.
This allows tracking multiple storage locations for the same part (e.g., different colors, spare parts).

Run this script once to update the database schema.
"""

import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "data" / "instance" / "brick_manager.db"

def migrate_database():
    """Add new columns to part_storage table."""
    
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(part_storage)")
        columns = [row[1] for row in cursor.fetchall()]
        
        changes_made = False
        
        # Add color_id column if it doesn't exist
        if 'color_id' not in columns:
            print("Adding color_id column to part_storage table...")
            cursor.execute("""
                ALTER TABLE part_storage 
                ADD COLUMN color_id INTEGER 
                REFERENCES rebrickable_colors(id)
            """)
            changes_made = True
            print("✓ color_id column added")
        else:
            print("✓ color_id column already exists")
        
        # Add notes column if it doesn't exist
        if 'notes' not in columns:
            print("Adding notes column to part_storage table...")
            cursor.execute("""
                ALTER TABLE part_storage 
                ADD COLUMN notes TEXT
            """)
            changes_made = True
            print("✓ notes column added")
        else:
            print("✓ notes column already exists")
        
        # Create index for faster lookups
        print("Creating index for part_storage lookups...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_part_location 
                ON part_storage(part_num, location, level, box)
            """)
            print("✓ Index created")
        except sqlite3.OperationalError as e:
            print(f"Note: Index creation - {e}")
        
        conn.commit()
        
        if changes_made:
            print("\n✅ Migration completed successfully!")
            print("\nYou can now:")
            print("  - Track parts in multiple locations")
            print("  - Specify color_id to distinguish color variants")
            print("  - Add notes (e.g., 'spare parts', 'red version')")
        else:
            print("\n✅ Database already up to date!")
        
    except sqlite3.Error as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Part Storage Migration Script")
    print("Adding support for multiple storage locations per part")
    print("=" * 60)
    print()
    
    migrate_database()
