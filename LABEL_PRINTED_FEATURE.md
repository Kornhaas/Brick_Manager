# Label Printed Feature

This document describes the new "Label Printed" feature added to the Bricks Manager application.

## Overview

The Label Printed feature allows users to track which items have had their labels printed. This helps manage label printing workflow and identify which items still need labels.

## Database Changes

Two tables have been updated with a new `label_printed` column:

### `user_sets` table
- Added `label_printed` BOOLEAN column (default: FALSE)
- Tracks whether a label has been printed for each user set

### `part_storage` table  
- Added `label_printed` BOOLEAN column (default: FALSE)
- Tracks whether a label has been printed for each part storage entry

## User Interface

### Box Maintenance Page
- Each part in a box now displays a "Label Printed" checkbox
- Users can check/uncheck to mark labels as printed or needing to be printed
- Status is saved automatically when checkbox is changed

### Set Maintenance Page
- User sets table now includes a "Label Printed" column
- Each set has a checkbox to mark if the label has been printed
- Status is saved automatically when checkbox is changed

## API Endpoints

### Box Maintenance
- `POST /box_maintenance/update_label_status`
  - Updates label_printed status for part storage entries
  - Body: `{"storage_id": int, "label_printed": boolean}`

### Set Maintenance  
- `POST /set_maintain/update_label_status`
  - Updates label_printed status for user sets
  - Body: `{"user_set_id": int, "label_printed": boolean}`

## Migration

A database migration has been created to add the new columns:
- File: `migrations/versions/001_add_label_printed.py`
- Adds `label_printed` column to both tables with default value FALSE

## Usage Workflow

1. **Initial State**: All items have `label_printed = FALSE`
2. **Generate Labels**: When users generate labels (existing functionality)
3. **Mark as Printed**: Users manually check the "Label Printed" checkbox
4. **Filter/Query**: Users can later identify which items need label reprinting

## Future Enhancements

Potential future improvements:
- Automatically mark labels as printed when generated
- Filter views to show only items needing labels
- Bulk operations to mark multiple items
- Label reprint tracking with timestamps