# Box Overview with Images - Feature Update

## What's New

Added **thumbnail images** to the Location and Level Overview cards to give you a visual preview of what's inside each box!

## Visual Design

### Card with Single Part
```
┌─────────────────────────┐
│   [Part Image]          │  ← Actual part image (150px height)
├─────────────────────────┤
│ Level 2 - Box 5         │
│ [1 part]                │
│ [View Details]          │
└─────────────────────────┘
```

### Card with Multiple Parts
```
┌─────────────────────────┐
│   [Part Image]   [+3 more]│  ← Orange badge in top-right corner
├─────────────────────────┤
│ Level 2 - Box 5         │
│ [4 parts]               │
│ [View Details]          │
└─────────────────────────┘
```

## Features

### **1. Part Images**
- Shows the **first part's image** from each box
- Images are **centered** and **contained** within 150px height (Location) or 120px (Level)
- Uses the same image priority as other parts of the app:
  1. RebrickableInventoryParts.img_url (color-specific images)
  2. RebrickableParts.part_img_url (generic part images)
  3. Default placeholder if no image available

### **2. Multiple Parts Indicator**
- When a box contains **more than 1 part**, an **orange badge** appears in the top-right corner
- Badge shows: `+X more` (e.g., "+3 more" means 4 total parts, showing 1 + 3 more)
- Badge uses **warning color** (orange/yellow) to stand out
- **Position**: Absolute positioning in top-right with margin

### **3. Enhanced Visual Feedback**
- **Light gray background** (#f8f9fa) behind images for consistency
- **Border** between image and card body
- **Hover effect** on entire card (lifts up with shadow)
- **Object-fit: contain** ensures images aren't distorted
- **Padding** around images for breathing room

### **4. Responsive Text**
- Part count badge now shows:
  - "1 part" (singular)
  - "2 parts" (plural)
  - "10 parts" (plural)

## Technical Implementation

### Backend Changes (`box_maintenance.py`)

#### Location Overview Endpoint
```python
@box_maintenance_bp.route("/box_maintenance/location_overview/<location>", methods=["GET"])
def get_location_overview(location):
    # Now queries the first part from each box
    # Returns img_url along with location, level, box, part_count
```

#### Level Overview Endpoint
```python
@box_maintenance_bp.route("/box_maintenance/level_overview/<location>/<level>", methods=["GET"])
def get_level_overview(location, level):
    # Now queries the first part from each box
    # Returns img_url along with location, level, box, part_count
```

### Frontend Changes (`box_maintenance_new.js`)

#### Card Generation Logic
```javascript
const multiplePartsHtml = box.part_count > 1 
    ? `<span class="badge bg-warning text-dark position-absolute top-0 end-0 m-2">+${box.part_count - 1} more</span>` 
    : '';

// Card structure with image and badge
<div class="position-relative">
    <img src="${box.img_url}" class="card-img-top" ...>
    ${multiplePartsHtml}
</div>
```

### CSS Enhancements (`box_maintenance_new.html`)

```css
.box-card {
    cursor: pointer;  /* Indicates clickability */
}

.box-card .card-img-top {
    background-color: #f8f9fa;  /* Light gray background */
    border-bottom: 1px solid #dee2e6;  /* Separator line */
}

.box-card .badge.position-absolute {
    font-size: 0.75rem;  /* Smaller badge text */
    padding: 0.35em 0.65em;  /* Comfortable padding */
}
```

## User Experience

### Location Overview
- **Grid of cards** showing all Level-Box combinations
- **Each card displays:**
  - Image of the first part in the box
  - Badge showing "+X more" if multiple parts
  - Level and Box identifier
  - Total part count
  - View Details button
- **Quick visual scanning** to identify boxes

### Level Overview
- **Compact grid** showing all boxes in a specific level
- **Smaller cards** (120px images vs 150px)
- **Same information** as Location Overview
- **Denser layout** for viewing many boxes at once

## Benefits

✅ **Visual Recognition** - Quickly identify boxes by part appearance
✅ **Information Density** - More info in less space
✅ **Better UX** - No need to click into each box to see what's inside
✅ **Professional Look** - Modern card design with images
✅ **Clear Indicators** - Orange badge clearly shows multiple parts
✅ **Consistent Styling** - Matches rest of application design

## Example Scenarios

### Scenario 1: Looking for Red Bricks
- Open Location Overview
- **Visually scan** the thumbnail images
- Spot the red brick image
- Click to view details

### Scenario 2: Finding a Full Box
- Open Level Overview
- See box cards with their images
- Cards with "+10 more" badge indicate fuller boxes
- Identify which boxes need reorganizing

### Scenario 3: Empty Box Detection
- Boxes with default placeholder image might need attention
- Quick visual scan shows which boxes have parts vs. empty

## Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (responsive design)

## Performance

- Images are **lazy-loaded** by browser
- **Thumbnail size** is optimized (150px/120px height)
- Uses **existing image URLs** from Rebrickable
- **No additional caching** needed (uses existing cache_service)

## Future Enhancements

Possible additions for the future:
1. **Multiple image preview** - Show 2-4 images in a grid
2. **Color indicators** - Border color based on part colors
3. **Image gallery modal** - Click image to see all parts
4. **Sorting by image** - Group similar-looking parts
5. **Thumbnail generation** - Custom thumbnails for better performance
