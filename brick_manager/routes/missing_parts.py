"""
This module handles the display of all missing parts and missing minifigure parts across all sets.
"""

import time
import urllib.parse
from flask import Blueprint, render_template, current_app, jsonify, request
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from models import db, User_Set, User_Parts, UserMinifigurePart, PartStorage, RebrickableParts, RebrickableColors, RebrickableInventories, RebrickableInventoryParts, RebrickablePartCategories
from services.part_lookup_service import load_part_lookup
from services.cache_service import cache_image
#pylint: disable=C0301
# Define a new Blueprint for missing parts
missing_parts_bp = Blueprint('missing_parts', __name__)


def enrich_missing_part(part, user_set, part_type='Regular Part'):
    """Helper function to enrich part data with proper images and color information"""
    try:
        current_app.logger.debug(f"Enriching {part_type} part: {part.part_num} for set {user_set.id}")
        
        
        storage_data = db.session.query(PartStorage).filter_by(part_num=part.part_num).first()
        current_app.logger.debug(f"Storage data found for {part.part_num}: {storage_data is not None}")
        
        # Get part info with proper joins to get color and image information
        part_query = db.session.query(
            RebrickableParts,
            RebrickableColors
        ).join(
            RebrickableColors, RebrickableColors.id == part.color_id
        ).filter(
            RebrickableParts.part_num == part.part_num
        ).first()
        
        part_info = part_query[0] if part_query else None
        color_info = part_query[1] if part_query else None
       
        # Try to get inventory-specific image URL
        inventory_img_url = None
        if user_set.template_set:
            inventory = RebrickableInventories.query.filter_by(set_num=user_set.template_set.set_num).first()
            if inventory:
                inv_part = RebrickableInventoryParts.query.filter_by(
                    inventory_id=inventory.id,
                    part_num=part.part_num,
                    color_id=part.color_id
                ).first()
                if inv_part and inv_part.img_url:
                    inventory_img_url = inv_part.img_url
        

        
        # Determine the best image URL (inventory-specific first, then generic part image)
        best_img_url = inventory_img_url or (part_info.part_img_url if part_info else None)
        
        # Use cache service to get cached image URL (or fallback if no image available)
        cached_img_url = cache_image(best_img_url) if best_img_url else '/static/default_image.png'
        
        
        master_lookup = load_part_lookup()
        part_data = master_lookup.get(part.part_num, {})
        location_data = (
            f"Location: {part_data.get('location', 'Unknown')}, "
            f"Level: {part_data.get('level', 'Unknown')}, "
            f"Box: {part_data.get('box', 'Unknown')}"
            if part_data else "Not Specified"
        )
        
        result = {
            'type': part_type,
            'set_id': user_set.template_set.set_num if user_set.template_set else 'Unknown',
            'internal_id': user_set.id,
            'item_id': part.part_num,
            'name': part_info.name if part_info else "Unknown",
            'category': part_info.category.name if part_info and hasattr(part_info, 'category') and part_info.category else "Unknown Category",
            'color': color_info.name if color_info else "Unknown",
            'color_rgb': color_info.rgb if color_info else "FFFFFF",
            'color_id': part.color_id,
            'is_spare': part.is_spare,
            'missing_quantity': part.quantity - part.have_quantity,
            'have_quantity': part.have_quantity,
            'total_quantity': part.quantity,
            'img_url': cached_img_url,
            'location': location_data,
            'status': "Available" if storage_data else "Not Available"
        }
        
        
        return result
        
    except Exception as e:
        current_app.logger.error(f"Error enriching part {part.part_num}: {str(e)}")
        # Return a basic result to prevent crashes
        return {
            'type': part_type,
            'set_id': user_set.template_set.set_num if hasattr(user_set, 'template_set') and user_set.template_set else 'Unknown',
            'internal_id': user_set.id,
            'item_id': part.part_num,
            'name': "Unknown",
            'category': "Unknown Category",
            'color': "Unknown",
            'color_rgb': "FFFFFF",
            'color_id': getattr(part, 'color_id', None),
            'is_spare': getattr(part, 'is_spare', False),
            'missing_quantity': part.quantity - part.have_quantity,
            'have_quantity': getattr(part, 'have_quantity', 0),
            'total_quantity': getattr(part, 'quantity', 0),
            'img_url': '/static/default_image.png',
            'location': "Not Specified",
            'status': "Not Available"
        }


def get_missing_parts_categories():
    """Get summary of missing parts grouped by category"""
    start_time = time.time()
    current_app.logger.info("Starting category summary analysis")
    
    categories = {}
    
    try:
        # Query all User_Sets to get missing regular parts by category
        query_start = time.time()
        user_sets = User_Set.query.all()
        query_time = time.time() - query_start
        current_app.logger.info(f"Queried {len(user_sets)} user sets in {query_time:.2f} seconds")
        
        # Process regular parts
        regular_start = time.time()
        for user_set in user_sets:
            if not hasattr(user_set, 'parts_in_set') or user_set.parts_in_set is None:
                continue
                
            for part in user_set.parts_in_set:
                if part.quantity > part.have_quantity:
                    # Get category information efficiently
                    part_info = db.session.query(RebrickableParts).filter_by(part_num=part.part_num).first()
                    if part_info and part_info.category:
                        category_name = part_info.category.name
                    else:
                        category_name = "Unknown Category"
                    
                    if category_name not in categories:
                        categories[category_name] = {'count': 0, 'total_missing': 0}
                    
                    categories[category_name]['count'] += 1
                    categories[category_name]['total_missing'] += (part.quantity - part.have_quantity)
        
        regular_time = time.time() - regular_start
        current_app.logger.info(f"Processed regular parts in {regular_time:.2f} seconds")
        
        # Process minifigure parts
        minifig_start = time.time()
        user_minifigure_parts = UserMinifigurePart.query.all()
        
        for minifig_part in user_minifigure_parts:
            if minifig_part.quantity > minifig_part.have_quantity:
                # Get category information efficiently
                part_info = db.session.query(RebrickableParts).filter_by(part_num=minifig_part.part_num).first()
                if part_info and part_info.category:
                    category_name = part_info.category.name
                else:
                    category_name = "Unknown Category"
                
                if category_name not in categories:
                    categories[category_name] = {'count': 0, 'total_missing': 0}
                
                categories[category_name]['count'] += 1
                categories[category_name]['total_missing'] += (minifig_part.quantity - minifig_part.have_quantity)
        
        minifig_time = time.time() - minifig_start
        current_app.logger.info(f"Processed minifigure parts in {minifig_time:.2f} seconds")
        
        # Convert to sorted list
        category_list = [
            {
                'name': name,
                'count': data['count'],
                'total_missing': data['total_missing']
            }
            for name, data in categories.items()
        ]
        category_list.sort(key=lambda x: x['name'])
        
        total_time = time.time() - start_time
        current_app.logger.info(f"Category summary complete in {total_time:.2f} seconds. Found {len(category_list)} categories")
        
        return category_list
        
    except Exception as e:
        current_app.logger.error(f"Error in get_missing_parts_categories: {str(e)}")
        current_app.logger.exception("Full traceback:")
        return []


@missing_parts_bp.route('/missing_parts_category/<path:category_name>', methods=['GET'])
def missing_parts_category(category_name):
    """Get missing parts for a specific category"""
    start_time = time.time()
    
    # URL decode the category name to handle special characters
    decoded_category_name = urllib.parse.unquote(category_name)
    current_app.logger.info(f"Getting missing parts for category: '{decoded_category_name}' (original: '{category_name}')")
    
    missing_items = []
    include_spare = request.args.get('include_spare', 'true').lower() == 'true'
    
    try:
        # Query all User_Sets for regular parts in this category
        user_sets = User_Set.query.all()
        
        for user_set in user_sets:
            if not hasattr(user_set, 'parts_in_set') or user_set.parts_in_set is None:
                continue
                
            for part in user_set.parts_in_set:
                if part.quantity > part.have_quantity:
                    # Skip spare parts if not requested
                    if not include_spare and part.is_spare:
                        continue
                        
                    # Check if this part belongs to the requested category
                    part_info = db.session.query(RebrickableParts).filter_by(part_num=part.part_num).first()
                    part_category = part_info.category.name if part_info and part_info.category else "Unknown Category"
                    
                    if part_category == decoded_category_name:
                        try:
                            enriched_part = enrich_missing_part(part, user_set, 'Regular Part')
                            missing_items.append(enriched_part)
                        except Exception as e:
                            current_app.logger.error(f"Error enriching regular part {part.part_num}: {str(e)}")
                            continue
        
        # Query minifigure parts in this category
        user_minifigure_parts = UserMinifigurePart.query.all()
        
        for minifig_part in user_minifigure_parts:
            if minifig_part.quantity > minifig_part.have_quantity:
                # Skip spare parts if not requested
                if not include_spare and minifig_part.is_spare:
                    continue
                    
                # Check if this part belongs to the requested category
                part_info = db.session.query(RebrickableParts).filter_by(part_num=minifig_part.part_num).first()
                part_category = part_info.category.name if part_info and part_info.category else "Unknown Category"
                
                if part_category == decoded_category_name:
                    try:
                        enriched_part = enrich_missing_part(minifig_part, minifig_part.user_set, 'Minifigure Part')
                        missing_items.append(enriched_part)
                    except Exception as e:
                        current_app.logger.error(f"Error enriching minifigure part {minifig_part.part_num}: {str(e)}")
                        continue
        
        # Sort by color
        missing_items.sort(key=lambda x: x['color'])
        
        total_time = time.time() - start_time
        current_app.logger.info(f"Retrieved {len(missing_items)} missing parts for category '{decoded_category_name}' in {total_time:.2f} seconds")
        
        return jsonify(missing_items)
        
    except Exception as e:
        current_app.logger.error(f"Error in missing_parts_category route: {str(e)}")
        current_app.logger.exception("Full traceback:")
        return jsonify([])


@missing_parts_bp.route('/missing_parts', methods=['GET'])
def missing_parts():
    """
    Displays category summary for missing parts and missing minifigure parts across all sets.
    """
    start_time = time.time()
    current_app.logger.info("Starting missing parts category analysis")
    
    try:
        categories = get_missing_parts_categories()
        total_time = time.time() - start_time
        current_app.logger.info(f"Missing parts category analysis complete in {total_time:.2f} seconds")
        
        return render_template('missing_parts.html', categories=categories)
        
    except Exception as e:
        current_app.logger.error(f"Error in missing_parts route: {str(e)}")
        current_app.logger.exception("Full traceback:")
        # Return empty categories to prevent crash
        return render_template('missing_parts.html', categories=[])


@missing_parts_bp.route('/update_part_quantity', methods=['POST'])
def update_part_quantity():
    """Update the have_quantity for a specific part"""
    try:
        data = request.get_json()
        part_id = data.get('part_id')
        set_id = int(data.get('set_id'))
        part_type = data.get('part_type')
        is_spare = data.get('is_spare', False)
        color_id = data.get('color_id')
        new_quantity = int(data.get('have_quantity'))
        
        current_app.logger.info(f"Updating {part_type} quantity: part={part_id}, set={set_id}, spare={is_spare}, color={color_id}, quantity={new_quantity}")
        
        if part_type == 'Regular Part':
            # Update regular part with more specific filtering
            query = User_Parts.query.filter_by(
                part_num=part_id,
                user_set_id=set_id,
                is_spare=is_spare
            )
            
            # Add color_id filter if provided
            if color_id:
                query = query.filter_by(color_id=int(color_id))
            
            part = query.first()
            
            if not part:
                current_app.logger.error(f"Regular part not found: part_num={part_id}, user_set_id={set_id}, is_spare={is_spare}, color_id={color_id}")
                return jsonify({'success': False, 'message': 'Part not found'}), 404
                
            part.have_quantity = new_quantity
            
        elif part_type == 'Minifigure Part':
            # Update minifigure part with more specific filtering
            query = UserMinifigurePart.query.filter_by(
                part_num=part_id,
                user_set_id=set_id,
                is_spare=is_spare
            )
            
            # Add color_id filter if provided
            if color_id:
                query = query.filter_by(color_id=int(color_id))
            
            part = query.first()
            
            if not part:
                current_app.logger.error(f"Minifigure part not found: part_num={part_id}, user_set_id={set_id}, is_spare={is_spare}, color_id={color_id}")
                return jsonify({'success': False, 'message': 'Minifigure part not found'}), 404
                
            part.have_quantity = new_quantity
            
        else:
            return jsonify({'success': False, 'message': 'Invalid part type'}), 400
        
        # Commit the changes
        db.session.commit()
        
        current_app.logger.info(f"Successfully updated {part_type} quantity for {part_id} in set {set_id} (spare: {is_spare})")
        
        return jsonify({
            'success': True, 
            'message': 'Quantity updated successfully',
            'total_quantity': part.quantity,
            'have_quantity': part.have_quantity,
            'missing_quantity': part.quantity - part.have_quantity
        })
        
    except ValueError as e:
        current_app.logger.error(f"Invalid data types in request: {str(e)}")
        return jsonify({'success': False, 'message': 'Invalid data format'}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating part quantity: {str(e)}")
        current_app.logger.exception("Full traceback:")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
