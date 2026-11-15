-- Cover the warehouse's part/color image lookup without rewriting catalog rows.
CREATE INDEX IF NOT EXISTS ix_inventory_part_color_image
ON rebrickable_inventory_parts (part_num, color_id, img_url);
