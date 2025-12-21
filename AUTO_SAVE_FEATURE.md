# Auto-Save Feature for Set Maintenance

## Overview
Implemented auto-save functionality for the Set Maintenance page, allowing quantity changes to be saved immediately to the database without requiring the "Save" button, matching the behavior of the Missing Parts page.

## Implementation

### Backend Changes

#### New Endpoint: `/set_maintain/update_part_quantity`
**File:** `brick_manager/routes/set_maintain.py`

- **Method:** POST
- **Accepts:** JSON with fields:
  - `part_id` (integer): The database ID of the part
  - `part_type` (string): Either "regular" or "minifig"
  - `have_quantity` (integer): The new quantity value
- **Returns:** JSON with:
  - `success` (boolean)
  - `message` (string)
  - `have_quantity` (integer): The actual saved value (clamped between 0 and max)
  - `total_quantity` (integer): The required quantity

**Key Features:**
- Automatically clamps values between 0 and the required quantity
- Handles both regular parts (`User_Parts`) and minifigure parts (`UserMinifigurePart`)
- Includes comprehensive error handling and logging
- Returns the clamped value so the UI can update accordingly

#### Import Addition
Added `User_Parts` to the imports in `set_maintain.py` to support the new endpoint.

### Frontend Changes

#### JavaScript Auto-Save Implementation
**File:** `brick_manager/static/js/set_maintenance.js`

**Key Changes:**

1. **Added CSS Classes to Input Fields**
   - Regular parts table: Added `auto-save-quantity` class and data attributes (`data-part-id`, `data-part-type="regular"`)
   - Minifig parts table: Added `auto-save-quantity` class and data attributes (`data-part-id`, `data-part-type="minifig"`)

2. **New Function: `attachAutoSaveListeners()`**
   - Attaches `change` event listeners to all quantity input fields
   - Prevents duplicate listeners by cloning and replacing nodes
   - Sends AJAX POST request to `/set_maintain/update_part_quantity` when value changes
   - Provides visual feedback:
     - Yellow border while saving
     - Green border on success (fades after 1 second)
     - Red border on error (fades after 2 seconds)
   - Updates row color based on completion:
     - `table-success` (green) when have_quantity ≥ total_quantity
     - `table-danger` (red) when incomplete
   - Updates input value with server-clamped value
   - Console logging for debugging

3. **Integration Points**
   - Called after regular parts table is populated
   - Called after minifig parts table is populated
   - Ensures all inputs have auto-save functionality

## User Experience

### Before
1. User clicks "View Details" for a set
2. User modifies quantity values
3. User must click "Save" button at bottom
4. Page refreshes
5. Changes are saved

### After
1. User clicks "View Details" for a set
2. User modifies a quantity value
3. **Change is saved automatically on blur/change**
4. Visual feedback shows save status
5. Row color updates based on completion
6. **No page refresh needed**
7. **No save button required** (though it still works)

## Visual Feedback

- **Yellow border**: Saving in progress
- **Green border (1s)**: Successfully saved
- **Red border (2s)**: Save failed
- **Row color change**: 
  - Red background → Green when part becomes complete
  - Green background → Red when part becomes incomplete

## Technical Benefits

1. **Immediate Persistence**: No risk of losing data if user navigates away
2. **Better UX**: No need to remember to click save
3. **Consistent**: Matches the Missing Parts page behavior
4. **Validation**: Server-side clamping ensures valid values
5. **Feedback**: Clear visual indication of save status
6. **Non-blocking**: Multiple fields can be edited in sequence
7. **Error Recovery**: Failed saves are clearly indicated

## Testing

### Manual Testing
1. Navigate to Set Maintenance page
2. Click "View Details" on any set
3. Change a quantity value in any of the tables:
   - Non-Spare Parts
   - Spare Parts  
   - Minifigure Parts
4. Observe:
   - Input border turns yellow briefly
   - Input border turns green on success
   - Row color changes if part becomes complete/incomplete
5. Refresh the page and verify value persisted
6. Test edge cases:
   - Value > max (should clamp to max)
   - Value < 0 (should clamp to 0)
   - Non-numeric input

### Automated Testing
```bash
# Test regular part update
curl -X POST http://127.0.0.1:5001/set_maintain/update_part_quantity \
  -H "Content-Type: application/json" \
  -d '{"part_id": 1, "part_type": "regular", "have_quantity": 5}'

# Expected response:
# {"have_quantity":1,"message":"Quantity updated successfully","success":true,"total_quantity":1}
# (Note: value clamped to max of 1)

# Test minifig part update
curl -X POST http://127.0.0.1:5001/set_maintain/update_part_quantity \
  -H "Content-Type: application/json" \
  -d '{"part_id": 1, "part_type": "minifig", "have_quantity": 1}'
```

## Files Modified

1. `/workspaces/Brick_Manager/brick_manager/routes/set_maintain.py`
   - Added `User_Parts` import
   - Added `/set_maintain/update_part_quantity` endpoint

2. `/workspaces/Brick_Manager/brick_manager/static/js/set_maintenance.js`
   - Added `auto-save-quantity` class to input fields
   - Added data attributes for part_id and part_type
   - Added `attachAutoSaveListeners()` function
   - Added auto-save calls after table population

## Compatibility

- **Backwards Compatible**: The existing "Save" button still works
- **Progressive Enhancement**: If JavaScript fails, form still submits normally
- **Database**: No schema changes required
- **API**: New endpoint doesn't affect existing functionality

## Future Enhancements

Potential improvements:
- Debouncing for rapid changes (wait 500ms before saving)
- Batch updates for multiple rapid changes
- Offline support with queue
- Undo/redo functionality
- Success toast notifications instead of border colors
- Loading indicator for slow connections
