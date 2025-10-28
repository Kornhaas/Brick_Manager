# Internal ID Filtering Feature for Missing Parts

## Overview
The missing parts page now supports filtering by specific internal IDs (the Internal ID column), allowing you to focus on missing parts from particular user sets or ranges of internal IDs.

## How to Use

### 1. Access the Feature
Navigate to the "Missing Parts" page in your Brick Manager application.

### 2. Internal ID Filter Input
You'll find an "Internal ID Filter" section with an input field that supports multiple formats:

### 3. Supported Filter Formats

#### Single Internal ID
```
229
```
Shows missing parts only from the user set with internal ID 229.

#### Range of Internal IDs
```
200-220
```
Shows missing parts from user sets with internal IDs 200 through 220 (inclusive).

#### List of Specific Internal IDs
```
200;204;205
```
or
```
200,204,205
```
Shows missing parts from user sets with internal IDs 200, 204, and 205 only.

#### Mixed Formats
```
200-210;229;250-260
```
Shows missing parts from user sets with internal IDs:
- 200 through 210
- 229
- 250 through 260

### 4. Apply Filter
- Click "Apply Filter" to apply the internal ID filter
- Click "Clear" to remove the filter and show all user sets
- The filter works together with the "Spare Parts" toggle

### 5. Filter Persistence
- The filter persists when switching between the category overview and detailed views
- The current filter is displayed in a blue info box when active
- URL parameters preserve the filter state for bookmarking/sharing

## Examples

### Use Case 1: Focus on a Single User Set
If you're working on the user set with internal ID 229, enter `229` in the filter to see only missing parts from that user set.

### Use Case 2: Focus on a Range of User Sets
For user sets in the 200s range, enter `200-299` to see missing parts from all user sets in that internal ID range.

### Use Case 3: Focus on Specific User Sets
If you're working on user sets with internal IDs 200, 204, and 205, enter `200;204;205` to see only missing parts from those specific user sets.

## Important Note

This filter uses **Internal IDs** (the unique identifier for each user set instance), not the LEGO set numbers. Each user set has its own internal ID which you can see in the "Internal ID" column of the missing parts table.

## Technical Details

### Backend Changes
- Added `parse_internal_id_filter()` function to handle various filter formats
- Updated `get_missing_parts_categories()` to accept internal ID filtering
- Modified category and API routes to support internal ID filtering
- Updated `should_include_set()` helper function to filter by internal ID

### Frontend Changes
- Updated filter input form with internal ID examples
- Updated JavaScript to include internal ID filter in AJAX requests
- Enhanced user interface with format examples and current filter display

### Performance
- Internal ID filtering is applied at the application level for optimal performance
- Filter parsing handles invalid input gracefully with logging
- Large ID ranges are supported efficiently

## Error Handling
- Invalid internal IDs are logged and ignored
- Invalid range formats are skipped with warnings
- Empty or malformed filters are treated as "no filter"
- JavaScript includes error handling for failed requests