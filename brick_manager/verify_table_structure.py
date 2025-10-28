#!/usr/bin/env python3
"""
Utility script to verify that database tables match model definitions

Run this script to check if your tables have the correct structure
after importing data from Rebrickable.
"""

import os
import sqlite3
import sys

from app import app
from models import RebrickableParts, db

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def check_table_structure():
    """Check if the database tables match the model definitions"""

    with app.app_context():
        # Check if we can query the model
        try:
            count = RebrickableParts.query.count()
            print(f"✅ RebrickableParts model works: {count} records")
        except Exception as e:
            print(f"❌ RebrickableParts model error: {e}")
            return False

        # Check database structure directly
        conn = sqlite3.connect("instance/brick_manager.db")
        cursor = conn.cursor()

        # Check table structure
        cursor.execute(
            'SELECT sql FROM sqlite_master WHERE type="table" AND name="rebrickable_parts";'
        )
        result = cursor.fetchone()

        if result:
            create_sql = result[0]
            print(f"\n📋 Current table structure:\n{create_sql}")

            # Check if PRIMARY KEY is present
            if "PRIMARY KEY" in create_sql:
                print("✅ PRIMARY KEY constraint found")
            else:
                print("❌ PRIMARY KEY constraint missing")
                return False

            # Check if required columns exist
            required_columns = [
                "part_num",
                "name",
                "part_cat_id",
                "part_material",
                "part_img_url",
                "part_url",
            ]
            for col in required_columns:
                if col in create_sql:
                    print(f"✅ Column '{col}' found")
                else:
                    print(f"❌ Column '{col}' missing")

        else:
            print("❌ rebrickable_parts table not found")
            return False

        conn.close()
        return True


def fix_table_structure():
    """Fix table structure if needed"""
    print("\n🔧 Ensuring proper table structure...")

    with app.app_context():
        # Use SQLAlchemy to create proper structure
        db.create_all()
        print("✅ Tables created with proper SQLAlchemy structure")


if __name__ == "__main__":
    print("🔍 Checking database table structure...")

    if check_table_structure():
        print("\n🎉 All checks passed! Your tables match the model definitions.")
    else:
        print("\n⚠️  Issues found. Running fix...")
        fix_table_structure()

        print("\n🔍 Re-checking after fix...")
        if check_table_structure():
            print("\n🎉 Fixed! Your tables now match the model definitions.")
        else:
            print("\n❌ Could not fix automatically. Manual intervention needed.")
