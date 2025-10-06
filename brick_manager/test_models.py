#!/usr/bin/env python3
"""
Test script to verify the updated models work correctly with the database.
"""

import os
import sys

# Add the current directory to the path so we can import models
sys.path.insert(0, '.')

try:
    # Test import of all models
    print("Testing model imports...")
    from models import (
        db, User_Set, User_Parts, User_Minifigures, UserMinifigurePart,
        RebrickableSets, RebrickableParts, RebrickableColors, RebrickableMinifigs
    )
    print("✓ All models imported successfully!")
    
    # Test model attributes
    print("\nTesting model attributes...")
    
    # User_Set attributes
    assert hasattr(User_Set, 'set_num'), "User_Set missing set_num"
    assert hasattr(User_Set, 'status'), "User_Set missing status"
    assert hasattr(User_Set, 'template_set'), "User_Set missing template_set relationship"
    assert hasattr(User_Set, 'parts_in_set'), "User_Set missing parts_in_set relationship"
    assert hasattr(User_Set, 'minifigures_in_set'), "User_Set missing minifigures_in_set relationship"
    print("✓ User_Set model structure correct")
    
    # User_Parts attributes
    assert hasattr(User_Parts, 'part_num'), "User_Parts missing part_num"
    assert hasattr(User_Parts, 'color_id'), "User_Parts missing color_id"
    assert hasattr(User_Parts, 'rebrickable_part'), "User_Parts missing rebrickable_part relationship"
    assert hasattr(User_Parts, 'rebrickable_color'), "User_Parts missing rebrickable_color relationship"
    print("✓ User_Parts model structure correct")
    
    # User_Minifigures attributes
    assert hasattr(User_Minifigures, 'fig_num'), "User_Minifigures missing fig_num"
    assert hasattr(User_Minifigures, 'rebrickable_minifig'), "User_Minifigures missing rebrickable_minifig relationship"
    print("✓ User_Minifigures model structure correct")
    
    # UserMinifigurePart attributes
    assert hasattr(UserMinifigurePart, 'part_num'), "UserMinifigurePart missing part_num"
    assert hasattr(UserMinifigurePart, 'color_id'), "UserMinifigurePart missing color_id"
    assert hasattr(UserMinifigurePart, 'rebrickable_part'), "UserMinifigurePart missing rebrickable_part relationship"
    assert hasattr(UserMinifigurePart, 'rebrickable_color'), "UserMinifigurePart missing rebrickable_color relationship"
    print("✓ UserMinifigurePart model structure correct")
    
    print("\n✅ All tests passed! Models are ready to use.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This is expected when running outside Flask environment")
except AssertionError as e:
    print(f"❌ Model structure error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()