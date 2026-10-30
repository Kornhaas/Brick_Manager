# Location Edit Feature

## Overview
Added a new feature to the Set Maintenance page that allows users to click on location cells in the parts tables to edit or add part location information via a popup modal.

## Implementation Details

### Backend Changes

#### 1. New Endpoint: `/update_part_location`
**File:** `brick_manager/routes/set_maintain.py`

- **Method:** POST
- **Accepts:** JSON with fields: `part_num`, `location`, `level`, `box`
- **Returns:** JSON with `success`, `location` (formatted string), and `message`

**Functionality:**
- Queries the `PartStorage` table for an existing entry with the given `part_num`
- If found, updates the `location`, `level`, and `box` fields
- If not found, creates a new `PartStorage` entry
- Returns a formatted location string (e.g., "Location: A, Level: 1, Box: 5")
- Includes error handling with database rollback on exceptions

### Frontend Changes

#### 2. Location Edit Modal
**File:** `brick_manager/templates/set_maintain.html`

Added a Bootstrap modal with:
- Display fields for part number and part name
- Input fields for:
  - Location (text input)
  - Level (text input)
  - Box (text input)
- Save and Cancel buttons
- Status alert area for success/error messages

#### 3. JavaScript Implementation
**File:** `brick_manager/static/js/set_maintenance.js`

**Key Functions:**

1. **`addLocationClickHandlers()`**
   - Adds click event listeners to all location cells in:
     - Non-spare parts table (column 8)
     - Spare parts table (column 8)
     - Minifig parts tables (column 7)
   - Sets cursor to pointer and adds tooltip
   - On click:
     - Extracts part number, name, and current location from the row
     - Parses current location into location/level/box components
     - Populates the modal with current values
     - Shows the modal

2. **Save Location Handler**
   - Attached to the "Save" button in the modal
   - Collects values from input fields
   - Sends POST request to `/update_part_location` endpoint
   - On success:
     - Updates the cell text with the new location
     - Shows success message
     - Closes modal after 1.5 seconds
   - On error:
     - Displays error message in the modal

3. **Initialization**
   - Hooks into existing "View Details" button click events
   - Calls `addLocationClickHandlers()` after parts tables are populated

## User Experience

1. User clicks "View Details" for a set
2. Parts tables are displayed with location information
3. User clicks on any location cell (shows pointer cursor)
4. Modal popup appears showing:
   - Part number and name (read-only)
   - Current location values (editable)
5. User enters or modifies location data
6. User clicks "Save"
7. Location is updated in database
8. Cell text updates immediately
9. Success message displays briefly
10. Modal closes automatically

## Testing

### Manual Testing Steps

1. Navigate to Set Maintenance page
2. Click "View Details" on any set
3. Find a part with "Not Specified" location
4. Click on the location cell
5. Enter location data (e.g., Location: "A", Level: "1", Box: "5")
6. Click "Save"
7. Verify the cell updates to show "Location: A, Level: 1, Box: 5"
8. Refresh the page and verify the location persists

### Automated Testing

Backend endpoint test:
```bash
curl -X POST http://127.0.0.1:5001/update_part_location \
  -H "Content-Type: application/json" \
  -d '{"part_num": "3001", "location": "A", "level": "1", "box": "5"}'
```

Expected response:
```json
{
  "location": "Location: A, Level: 1, Box: 5",
  "message": "Location updated successfully",
  "success": true
}
```

## Database Schema

The feature uses the existing `PartStorage` model with fields:
- `id` (Integer, Primary Key)
- `part_num` (Text, Foreign Key to rebrickable_parts)
- `location` (Text)
- `level` (Text)
- `box` (Text)
- `color_id` (Integer, optional)
- `notes` (Text, nullable)
- `label_printed` (Boolean, default False)

## Files Modified

1. `/workspaces/Brick_Manager/brick_manager/routes/set_maintain.py` - Added endpoint
2. `/workspaces/Brick_Manager/brick_manager/templates/set_maintain.html` - Added modal
3. `/workspaces/Brick_Manager/brick_manager/static/js/set_maintenance.js` - Added JavaScript handlers

## Benefits

- **No page refresh required** - Updates happen via AJAX
- **User-friendly** - Click-to-edit interface with modal popup
- **Persistent** - Data stored in SQLite database
- **Flexible** - Can add or update locations for any part
- **Immediate feedback** - Success/error messages displayed instantly

## Future Enhancements

Potential improvements:
- Add autocomplete for location names based on existing entries
- Add validation for level and box (numeric values)
- Add ability to clear/reset location
- Add bulk location update for multiple parts
- Add location history tracking
- Add color-specific location tracking
