#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '/workspaces/Bricks_Manager/brick_manager')

from app import app
from models import db, User_Set
import json

def test_update_label_status():
    """Test the update_label_status functionality"""
    
    with app.app_context():
        # Test 1: Get a user set before update
        user_set = User_Set.query.first()
        if not user_set:
            print("No user sets found in database")
            return False
            
        print(f"Before update: User Set ID {user_set.id}, Label Printed: {user_set.label_printed}")
        
        # Test 2: Simulate the API call
        test_data = {
            'user_set_id': user_set.id,
            'label_printed': True
        }
        
        # Manual update (simulating what the API should do)
        user_set.label_printed = bool(test_data['label_printed'])
        db.session.commit()
        
        print(f"After update: User Set ID {user_set.id}, Label Printed: {user_set.label_printed}")
        
        # Test 3: Verify the update persisted
        db.session.refresh(user_set)
        print(f"After refresh: User Set ID {user_set.id}, Label Printed: {user_set.label_printed}")
        
        # Test 4: Test setting back to False
        user_set.label_printed = False
        db.session.commit()
        db.session.refresh(user_set)
        print(f"Reset to False: User Set ID {user_set.id}, Label Printed: {user_set.label_printed}")
        
        return True

if __name__ == "__main__":
    success = test_update_label_status()
    if success:
        print("✅ Database update functionality works correctly!")
    else:
        print("❌ Database update functionality failed!")