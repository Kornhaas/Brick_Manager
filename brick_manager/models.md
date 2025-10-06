# Brick Manager Database ER Diagram

```mermaid
erDiagram
# Brick Manager Database ER Diagram

```mermaid
erDiagram
    REBRICKABLE_SETS ||--o{ USER_SETS : template
    USER_SETS ||--o{ USER_PARTS : contains
    REBRICKABLE_PARTS ||--o{ USER_PARTS : part
    REBRICKABLE_COLORS ||--o{ USER_PARTS : color
    USER_SETS ||--o{ USER_MINIFIGURES : contains
    REBRICKABLE_MINIFIGS ||--o{ USER_MINIFIGURES : minifig
    USER_SETS ||--o{ USER_MINIFIGURE_PARTS : contains
    REBRICKABLE_PARTS ||--o{ USER_MINIFIGURE_PARTS : part
    REBRICKABLE_COLORS ||--o{ USER_MINIFIGURE_PARTS : color
    REBRICKABLE_PARTS ||--o{ PART_STORAGE : stored

    REBRICKABLE_PART_CATEGORIES ||--o{ REBRICKABLE_PARTS : contains
    REBRICKABLE_COLORS ||--o{ REBRICKABLE_ELEMENTS : colors
    REBRICKABLE_PARTS ||--o{ REBRICKABLE_ELEMENTS : has
    REBRICKABLE_PARTS ||--o{ REBRICKABLE_PART_RELATIONSHIPS : child
    REBRICKABLE_PARTS ||--o{ REBRICKABLE_PART_RELATIONSHIPS : parent
    REBRICKABLE_THEMES ||--o{ REBRICKABLE_SETS : theme
    REBRICKABLE_THEMES ||--o{ REBRICKABLE_THEMES : parent_theme
    REBRICKABLE_SETS ||--o{ REBRICKABLE_INVENTORIES : inventories
    REBRICKABLE_INVENTORIES ||--o{ REBRICKABLE_INVENTORY_PARTS : inventory
    REBRICKABLE_PARTS ||--o{ REBRICKABLE_INVENTORY_PARTS : part
    REBRICKABLE_COLORS ||--o{ REBRICKABLE_INVENTORY_PARTS : color
    REBRICKABLE_INVENTORIES ||--o{ REBRICKABLE_INVENTORY_SETS : inventory
    REBRICKABLE_SETS ||--o{ REBRICKABLE_INVENTORY_SETS : set
    REBRICKABLE_INVENTORIES ||--o{ REBRICKABLE_INVENTORY_MINIFIGS : inventory
    REBRICKABLE_MINIFIGS ||--o{ REBRICKABLE_INVENTORY_MINIFIGS : minifig

    USER_SETS {
        int id PK
        string set_num FK
        string status
    }
    USER_PARTS {
        int id PK
        string part_num FK
        int color_id FK
        int quantity
        int have_quantity
        int user_set_id FK
        bool is_spare
    }
    USER_MINIFIGURES {
        int id PK
        string fig_num FK
        int quantity
        int have_quantity
        int user_set_id FK
    }
    USER_MINIFIGURE_PARTS {
        int id PK
        string part_num FK
        int color_id FK
        int quantity
        int have_quantity
        int user_set_id FK
        bool is_spare
    }
    PART_STORAGE {
        int id PK
        string part_num FK
        string location
        string level
        string box
    }

    REBRICKABLE_PART_CATEGORIES {
        int id PK
        text name
    }
    REBRICKABLE_COLORS {
        int id PK
        text name
        text rgb
        bool is_trans
        int num_parts
        int num_sets
        float y1
        float y2
    }
    REBRICKABLE_PARTS {
        text part_num PK
        text name
        int part_cat_id FK
        text part_material
        text part_img_url
        text part_url
    }
    REBRICKABLE_PART_RELATIONSHIPS {
        text rel_type PK
        text child_part_num PK, FK
        text parent_part_num PK, FK
    }
    REBRICKABLE_ELEMENTS {
        text element_id PK
        text part_num FK
        int color_id FK
        text design_id
    }
    REBRICKABLE_THEMES {
        int id PK
        text name
        int parent_id FK
    }
    REBRICKABLE_SETS {
        text set_num PK
        text name
        int year
        int theme_id FK
        int num_parts
        text img_url
    }
    REBRICKABLE_MINIFIGS {
        text fig_num PK
        text name
        int num_parts
        text img_url
    }
    REBRICKABLE_INVENTORIES {
        int id PK
        int version
        text set_num
    }
    REBRICKABLE_INVENTORY_PARTS {
        int inventory_id PK, FK
        text part_num PK, FK
        int color_id PK, FK
        int quantity
        bool is_spare PK
        text img_url
    }
    REBRICKABLE_INVENTORY_SETS {
        int inventory_id PK, FK
        text set_num PK, FK
        int quantity
    }
    REBRICKABLE_INVENTORY_MINIFIGS {
        int inventory_id PK, FK
        text fig_num PK, FK
        int quantity
    }
```
