"""
Rebrickable synchronization service for syncing missing parts with Rebrickable's Lost Parts feature.

This service handles the synchronization of missing parts from the local database
with the user's Lost Parts list on Rebrickable.
"""

import logging
import requests
import time
from models import db, User_Set, User_Parts, UserMinifigurePart, RebrickableParts
from services.token_service import get_rebrickable_user_token, get_rebrickable_api_key

logger = logging.getLogger(__name__)

# Global rate limiting tracker
_rate_limit_tracker = {
    'consecutive_hits': 0,
    'last_hit_time': 0,
    'should_throttle': False
}

def update_rate_limit_tracker(was_rate_limited):
    """Update the global rate limiting tracker."""
    global _rate_limit_tracker
    
    if was_rate_limited:
        _rate_limit_tracker['consecutive_hits'] += 1
        _rate_limit_tracker['last_hit_time'] = time.time()
        # Start throttling after 3 consecutive hits
        if _rate_limit_tracker['consecutive_hits'] >= 3:
            _rate_limit_tracker['should_throttle'] = True
    else:
        _rate_limit_tracker['consecutive_hits'] = 0
        _rate_limit_tracker['should_throttle'] = False

def should_skip_api_calls():
    """Check if we should skip API calls due to rate limiting."""
    global _rate_limit_tracker
    
    if _rate_limit_tracker['should_throttle']:
        # Reset throttling after 30 seconds
        if time.time() - _rate_limit_tracker['last_hit_time'] > 30:
            _rate_limit_tracker['should_throttle'] = False
            _rate_limit_tracker['consecutive_hits'] = 0
            return False
        return True
    return False

def find_inventory_part_id_from_user_sets(part_num, color_id, user_set_num=None):
    """
    Find an inventory part ID for a given part number and color ID from the user's actual sets.
    This is the most accurate method since we're looking in sets the user actually owns.
    
    Args:
        part_num: The part number to find
        color_id: The color ID to find  
        user_set_num: If provided, look in this specific set first
    """
    try:
        # Check if we should skip API calls due to rate limiting
        if should_skip_api_calls():
            logger.debug(f"Skipping API calls for {part_num}/{color_id} due to rate limiting")
            return None
        
        api_key = get_rebrickable_api_key()
        if not api_key:
            logger.error("Missing Rebrickable API key")
            return None
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        # If we have a specific set number, check that set first
        sets_to_check = []
        if user_set_num:
            sets_to_check.append(user_set_num)
        
        # Also get a few other sets that contain this part as backup
        try:
            backup_sets_url = f'https://rebrickable.com/api/v3/lego/parts/{part_num}/colors/{color_id}/sets/'
            backup_response = make_rate_limited_request(backup_sets_url, headers, {'page_size': 5}, timeout=20)
            if backup_response and backup_response.status_code == 200:
                backup_data = backup_response.json()
                for set_info in backup_data.get('results', [])[:3]:  # Just try 3 backup sets
                    if set_info['set_num'] not in sets_to_check:
                        sets_to_check.append(set_info['set_num'])
                update_rate_limit_tracker(False)  # Success
            elif backup_response and backup_response.status_code == 429:
                logger.debug(f"Rate limited when looking up backup sets for {part_num}/{color_id}")
                update_rate_limit_tracker(True)  # Rate limited
                # Continue with just the user_set_num if we have it
        except:
            pass  # If backup lookup fails, continue with what we have
        
        # Try each set until we find the part
        for set_num in sets_to_check:
            # Check rate limiting before each API call
            if should_skip_api_calls():
                logger.debug(f"Stopping set checks for {part_num}/{color_id} due to rate limiting")
                break
                
            try:
                inv_url = f'https://rebrickable.com/api/v3/lego/sets/{set_num}/parts/'
                # Filter for the specific part and color to reduce response size
                params = {
                    'part_num': part_num,
                    'page_size': 100
                }
                
                inv_response = make_rate_limited_request(inv_url, headers, params, timeout=20)
                
                if inv_response and inv_response.status_code == 200:
                    inv_data = inv_response.json()
                    
                    # Find the exact part+color match
                    for inv_part in inv_data.get('results', []):
                        if (inv_part['part']['part_num'] == part_num and 
                            inv_part['color']['id'] == color_id):
                            logger.debug(f"Found inv_part_id {inv_part['id']} for {part_num}/{color_id} in set {set_num}")
                            update_rate_limit_tracker(False)  # Success
                            return inv_part['id']
                    update_rate_limit_tracker(False)  # Success but no match
                elif inv_response and inv_response.status_code == 429:
                    logger.debug(f"Rate limited when checking set {set_num} for {part_num}/{color_id}")
                    update_rate_limit_tracker(True)  # Rate limited
                    # Break out of loop if we hit rate limits to avoid further API calls
                    break
                            
            except Exception as e:
                logger.debug(f"Error checking set {set_num}: {e}")
                continue
        
        logger.debug(f"Could not find inventory part ID for {part_num} in color {color_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error finding inventory part ID for {part_num}/{color_id}: {e}")
        return None


def make_rate_limited_request(url, headers, params=None, timeout=20, max_retries=3, method='GET'):
    """
    Make an HTTP request with automatic rate limiting and retry logic.
    
    Args:
        url: Request URL
        headers: HTTP headers
        params: Query parameters
        timeout: Request timeout
        max_retries: Maximum number of retries on rate limit
        method: HTTP method (GET, POST, DELETE, etc.)
    
    Returns:
        requests.Response or None if rate limited and retries exhausted
    """
    import time
    
    for attempt in range(max_retries + 1):
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, params=params, timeout=timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code == 429:
                if attempt < max_retries:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2 ** attempt
                    logger.debug(f"Rate limited (attempt {attempt + 1}/{max_retries + 1}), waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.debug(f"Rate limited after {max_retries + 1} attempts, giving up")
                    return response  # Return the 429 response
            else:
                return response
                
        except Exception as e:
            logger.debug(f"Request failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)


def get_local_missing_parts(include_spare=False):
    """
    Get all missing parts from the local database (excluding spare parts by default).
    Returns a list of parts with their missing quantities.
    """
    missing_parts = []
    
    try:
        # Get missing regular parts from user sets
        user_sets = User_Set.query.all()
        
        for user_set in user_sets:
            if not hasattr(user_set, 'parts_in_set') or user_set.parts_in_set is None:
                continue
                
            for part in user_set.parts_in_set:
                if part.quantity > part.have_quantity:
                    # Skip spare parts if not requested
                    if not include_spare and getattr(part, 'is_spare', False):
                        continue
                    
                    missing_quantity = part.quantity - part.have_quantity
                    missing_parts.append({
                        'part_num': part.part_num,
                        'color_id': part.color_id,
                        'missing_quantity': missing_quantity,
                        'set_num': user_set.set_num,
                        'is_spare': getattr(part, 'is_spare', False)
                    })
        
        # Get missing minifigure parts
        user_minifigure_parts = UserMinifigurePart.query.all()
        
        for minifig_part in user_minifigure_parts:
            if minifig_part.quantity > minifig_part.have_quantity:
                # Skip spare parts if not requested
                if not include_spare and getattr(minifig_part, 'is_spare', False):
                    continue
                
                missing_quantity = minifig_part.quantity - minifig_part.have_quantity
                missing_parts.append({
                    'part_num': minifig_part.part_num,
                    'color_id': minifig_part.color_id,
                    'missing_quantity': missing_quantity,
                    'set_num': None,  # Minifig parts don't have direct set association
                    'is_spare': getattr(minifig_part, 'is_spare', False),
                    'is_minifig': True
                })
        
        logger.info(f"Found {len(missing_parts)} missing parts locally")
        return missing_parts
        
    except Exception as e:
        logger.error(f"Error getting local missing parts: {e}")
        return []

def get_rebrickable_lost_parts():
    """
    Get all lost parts from Rebrickable for the current user.
    """
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            logger.error("Missing Rebrickable credentials")
            return []
        
        url = f'https://rebrickable.com/api/v3/users/{user_token}/lost_parts/'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        all_lost_parts = []
        page = 1
        
        while True:
            response = requests.get(url, headers=headers, params={'page': page}, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to get lost parts from Rebrickable: {response.status_code} - {response.text}")
                break
            
            data = response.json()
            all_lost_parts.extend(data.get('results', []))
            
            # Check if there are more pages
            if not data.get('next'):
                break
            page += 1
        
        logger.info(f"Found {len(all_lost_parts)} lost parts on Rebrickable")
        return all_lost_parts
        
    except Exception as e:
        logger.error(f"Error getting Rebrickable lost parts: {e}")
        return []

def add_lost_parts_to_rebrickable(parts_to_add):
    """
    Add multiple lost parts to Rebrickable using bulk operations.
    Each part should have inv_part_id and missing_quantity.
    Uses intelligent batching for large numbers of parts to avoid timeouts.
    """
    if not parts_to_add:
        return {'success': True, 'added': 0, 'rate_limited_count': 0, 'message': 'No parts to add'}
    
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            return {'success': False, 'message': 'Missing Rebrickable credentials'}
        
        url = f'https://rebrickable.com/api/v3/users/{user_token}/lost_parts/'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        # Prepare the data for bulk addition
        parts_data = []
        for part in parts_to_add:
            if 'inv_part_id' in part:
                parts_data.append({
                    'inv_part_id': part['inv_part_id'],
                    'lost_quantity': part['missing_quantity']
                })
        
        if not parts_data:
            return {'success': False, 'message': 'No valid parts to add (missing inventory part IDs)'}
        
        logger.info(f"Adding {len(parts_data)} parts to Rebrickable lost parts using bulk API")
        
        # For large numbers of parts, use batch processing to avoid timeouts
        batch_size = 100  # Rebrickable can handle this many parts in one request
        total_added = 0
        total_rate_limited = 0
        total_errors = []
        
        for i in range(0, len(parts_data), batch_size):
            batch = parts_data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(parts_data) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} parts)")
            
            try:
                response = requests.post(url, headers=headers, json=batch, timeout=60)  # Longer timeout for batches
                
                if response.status_code == 201:
                    added_parts = response.json()
                    batch_added = len(added_parts)
                    total_added += batch_added
                    logger.info(f"Batch {batch_num}: Successfully added {batch_added} parts")
                    
                    # Update rate limiting tracker on success
                    update_rate_limit_tracker(False)
                    
                elif response.status_code == 429:
                    # Rate limited - try individual processing for this batch
                    logger.warning(f"Batch {batch_num} rate limited, trying individual requests")
                    individual_result = add_lost_parts_individually(batch, headers, user_token)
                    total_added += individual_result.get('added_count', 0)
                    total_rate_limited += individual_result.get('rate_limited_count', 0)
                    
                    # Update rate limiting tracker
                    update_rate_limit_tracker(True)
                    
                    # If individual processing also hits rate limits, stop batching
                    if individual_result.get('rate_limited_count', 0) > 0:
                        logger.warning(f"Rate limiting detected in batch {batch_num}, stopping remaining batches to preserve API quota")
                        remaining_parts = len(parts_data) - (i + len(batch))
                        if remaining_parts > 0:
                            total_rate_limited += remaining_parts
                            logger.info(f"Deferring {remaining_parts} remaining parts to next scheduled sync")
                        break
                        
                else:
                    error_msg = f"Batch {batch_num} failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    total_errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error in batch {batch_num}: {str(e)}"
                logger.error(error_msg)
                total_errors.append(error_msg)
                continue
        
        # Determine success based on results
        success = total_added > 0 or len(total_errors) == 0
        
        return {
            'success': success,
            'added': total_added,
            'rate_limited_count': total_rate_limited,
            'total_attempted': len(parts_data),
            'errors': total_errors,
            'message': f'Added {total_added}/{len(parts_data)} parts to lost parts. {total_rate_limited} parts rate limited (will retry on next sync).'
        }
            
    except Exception as e:
        logger.error(f"Error adding lost parts to Rebrickable: {e}")
        return {'success': False, 'message': f'Error adding parts: {str(e)}'}

def add_lost_parts_individually(parts_data, headers, user_token):
    """
    Add lost parts individually when bulk operation is rate limited.
    
    Args:
        parts_data: List of part dictionaries to add
        headers: HTTP headers for API requests
        user_token: Rebrickable user token
        
    Returns:
        dict: Result with success counts and rate limiting info
    """
    try:
        url = f'https://rebrickable.com/api/v3/users/{user_token}/lost_parts/'
        added_count = 0
        rate_limited_count = 0
        errors = []
        
        for i, part_data in enumerate(parts_data):
            try:
                response = requests.post(url, headers=headers, json=[part_data], timeout=20)
                
                if response.status_code == 201:
                    added_count += 1
                    logger.debug(f"Added part {part_data.get('inv_part_id')} to lost parts")
                elif response.status_code == 429:
                    # Rate limited - this is expected for large sync operations
                    rate_limited_count += 1
                    logger.info(f"Rate limited on part {part_data.get('inv_part_id')} (attempt {i+1}/{len(parts_data)})")
                    # Don't treat this as an error - just note it for summary
                else:
                    error_msg = f"Failed to add part {part_data.get('inv_part_id')}: {response.text}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error adding part {part_data.get('inv_part_id')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return {
            'success': True,
            'added': added_count,
            'rate_limited_count': rate_limited_count,
            'total_attempted': len(parts_data),
            'errors': errors,
            'message': f'Added {added_count}/{len(parts_data)} parts to lost parts. {rate_limited_count} parts hit rate limits (will be retried on next sync).'
        }
        
    except Exception as e:
        logger.error(f"Error during individual parts addition: {e}")
        return {
            'success': False,
            'message': f'Error adding parts individually: {str(e)}'
        }

def remove_lost_parts_from_rebrickable(parts_to_remove):
    """
    Remove multiple lost parts from Rebrickable.
    """
    if not parts_to_remove:
        return {'success': True, 'removed': 0, 'message': 'No parts to remove'}
    
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            return {'success': False, 'message': 'Missing Rebrickable credentials'}
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        removed_count = 0
        errors = []
        
        for part in parts_to_remove:
            lost_part_id = part.get('lost_part_id')
            if not lost_part_id:
                continue
                
            url = f'https://rebrickable.com/api/v3/users/{user_token}/lost_parts/{lost_part_id}/'
            response = requests.delete(url, headers=headers, timeout=30)
            
            if response.status_code == 204:
                removed_count += 1
            else:
                errors.append(f"Failed to remove part {lost_part_id}: {response.status_code}")
        
        if errors:
            logger.warning(f"Some parts failed to remove: {errors}")
        
        return {
            'success': True,
            'removed': removed_count,
            'errors': errors,
            'message': f'Removed {removed_count} parts from Rebrickable lost parts'
        }
        
    except Exception as e:
        logger.error(f"Error removing lost parts from Rebrickable: {e}")
        return {'success': False, 'message': f'Error removing parts: {str(e)}'}

def get_user_part_lists():
    """
    Get all part lists for the user.
    Returns a list of part lists or empty list if none found.
    """
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            logger.error("Missing Rebrickable credentials for part lists lookup")
            return []
        
        url = f'https://rebrickable.com/api/v3/users/{user_token}/partlists/'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        all_lists = []
        page = 1
        
        while True:
            params = {'page': page, 'page_size': 100}
            response = make_rate_limited_request(url, headers, params, timeout=20)
            
            if not response or response.status_code != 200:
                logger.error(f"Failed to get part lists: {response.status_code if response else 'No response'}")
                break
            
            data = response.json()
            all_lists.extend(data.get('results', []))
            
            if not data.get('next'):
                break
            page += 1
        
        logger.info(f"Found {len(all_lists)} part lists for user")
        return all_lists
        
    except Exception as e:
        logger.error(f"Error getting user part lists: {e}")
        return []


def find_or_create_missing_parts_list(list_name="Brick_Manager-Missing_Parts"):
    """
    Find existing missing parts list or create it if it doesn't exist.
    Returns the list ID or None if creation failed.
    """
    try:
        # First, check if the list already exists
        part_lists = get_user_part_lists()
        
        for part_list in part_lists:
            if part_list.get('name') == list_name:
                logger.info(f"Found existing part list '{list_name}' with ID {part_list['id']}")
                return part_list['id']
        
        # List doesn't exist, create it
        logger.info(f"Creating new part list '{list_name}'")
        
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            logger.error("Missing Rebrickable credentials for part list creation")
            return None
        
        url = f'https://rebrickable.com/api/v3/users/{user_token}/partlists/'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'name': list_name,
            'is_buildable': False,
            'num_parts': 0
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 201:
            created_list = response.json()
            list_id = created_list['id']
            logger.info(f"Successfully created part list '{list_name}' with ID {list_id}")
            update_rate_limit_tracker(False)
            return list_id
        else:
            logger.error(f"Failed to create part list: {response.status_code} - {response.text}")
            update_rate_limit_tracker(response.status_code == 429)
            return None
        
    except Exception as e:
        logger.error(f"Error finding or creating missing parts list: {e}")
        return None


def get_part_list_parts(list_id):
    """
    Get all parts from a specific part list.
    Returns a list of parts or empty list if none found.
    """
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            logger.error("Missing Rebrickable credentials for part list parts lookup")
            return []
        
        url = f'https://rebrickable.com/api/v3/users/{user_token}/partlists/{list_id}/parts/'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        all_parts = []
        page = 1
        
        while True:
            params = {'page': page, 'page_size': 100}
            response = make_rate_limited_request(url, headers, params, timeout=20)
            
            if not response or response.status_code != 200:
                logger.error(f"Failed to get part list parts: {response.status_code if response else 'No response'}")
                break
            
            data = response.json()
            all_parts.extend(data.get('results', []))
            
            if not data.get('next'):
                break
            page += 1
        
        logger.info(f"Found {len(all_parts)} parts in part list {list_id}")
        return all_parts
        
    except Exception as e:
        logger.error(f"Error getting part list parts: {e}")
        return []


def add_parts_to_part_list(list_id, parts_to_add):
    """
    Add multiple parts to a part list using bulk operations.
    Each part should have part_num, color_id, and quantity.
    Uses intelligent batching for large numbers of parts to avoid timeouts.
    """
    if not parts_to_add:
        return {'success': True, 'added': 0, 'rate_limited_count': 0, 'message': 'No parts to add'}
    
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            return {'success': False, 'message': 'Missing Rebrickable credentials'}
        
        url = f'https://rebrickable.com/api/v3/users/{user_token}/partlists/{list_id}/parts/'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        # Prepare the data for bulk addition
        parts_data = []
        for part in parts_to_add:
            parts_data.append({
                'part_num': part['part_num'],
                'color_id': part['color_id'],
                'quantity': part['missing_quantity']
            })
        
        logger.info(f"Adding {len(parts_data)} parts to part list {list_id} using bulk API")
        
        # For large numbers of parts, use batch processing to avoid timeouts
        batch_size = 100  # Rebrickable can handle this many parts in one request
        total_added = 0
        total_rate_limited = 0
        total_errors = []
        
        for i in range(0, len(parts_data), batch_size):
            batch = parts_data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(parts_data) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} parts)")
            
            try:
                response = requests.post(url, headers=headers, json=batch, timeout=60)
                
                if response.status_code == 201:
                    added_parts = response.json()
                    batch_added = len(added_parts)
                    total_added += batch_added
                    logger.info(f"Batch {batch_num}: Successfully added {batch_added} parts")
                    
                    # Update rate limiting tracker on success
                    update_rate_limit_tracker(False)
                    
                elif response.status_code == 429:
                    # Rate limited - try individual processing for this batch
                    logger.warning(f"Batch {batch_num} rate limited, trying individual requests")
                    individual_result = add_parts_individually_to_list(list_id, batch, headers, user_token)
                    total_added += individual_result.get('added_count', 0)
                    total_rate_limited += individual_result.get('rate_limited_count', 0)
                    
                    # Update rate limiting tracker
                    update_rate_limit_tracker(True)
                    
                    # If individual processing also hits rate limits, stop batching
                    if individual_result.get('rate_limited_count', 0) > 0:
                        logger.warning(f"Rate limiting detected in batch {batch_num}, stopping remaining batches")
                        remaining_parts = len(parts_data) - (i + len(batch))
                        if remaining_parts > 0:
                            total_rate_limited += remaining_parts
                            logger.info(f"Deferring {remaining_parts} remaining parts to next scheduled sync")
                        break
                        
                else:
                    error_msg = f"Batch {batch_num} failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    total_errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error in batch {batch_num}: {str(e)}"
                logger.error(error_msg)
                total_errors.append(error_msg)
                continue
        
        # Determine success based on results
        success = total_added > 0 or len(total_errors) == 0
        
        # Create comprehensive response
        result = {
            'success': success,
            'added': total_added,
            'rate_limited_count': total_rate_limited,
            'errors': total_errors,
            'total_attempted': len(parts_data)
        }
        
        if success:
            result['message'] = f"Successfully added {total_added} parts to part list"
            if total_rate_limited > 0:
                result['message'] += f" ({total_rate_limited} parts were rate limited and will be synced in next run)"
        else:
            result['message'] = f"Failed to add parts to part list. Errors: {'; '.join(total_errors[:3])}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error adding parts to part list: {e}")
        return {'success': False, 'message': f'Error adding parts: {str(e)}'}


def add_parts_individually_to_list(list_id, parts_data, headers, user_token):
    """
    Fallback function to add parts individually when bulk operations are rate limited.
    """
    added_count = 0
    rate_limited_count = 0
    
    for part in parts_data:
        if should_skip_api_calls():
            rate_limited_count += 1
            continue
        
        try:
            url = f'https://rebrickable.com/api/v3/users/{user_token}/partlists/{list_id}/parts/'
            data = {
                'part_num': part['part_num'],
                'color_id': part['color_id'],
                'quantity': part['quantity']
            }
            
            # Use form data for individual requests
            headers_form = headers.copy()
            headers_form['Content-Type'] = 'application/x-www-form-urlencoded'
            
            response = requests.post(url, headers=headers_form, data=data, timeout=30)
            
            if response.status_code == 201:
                added_count += 1
                update_rate_limit_tracker(False)
            elif response.status_code == 429:
                rate_limited_count += 1
                update_rate_limit_tracker(True)
                logger.debug(f"Rate limited adding individual part {part['part_num']}/{part['color_id']}")
            else:
                logger.debug(f"Failed to add individual part {part['part_num']}/{part['color_id']}: {response.status_code}")
                
        except Exception as e:
            logger.debug(f"Error adding individual part: {e}")
            continue
    
    return {'added_count': added_count, 'rate_limited_count': rate_limited_count}


def clear_part_list(list_id):
    """
    Remove all parts from a part list using the most efficient method available.
    First tries to delete and recreate the list (fastest), falls back to individual deletions.
    Returns success status and count of removed parts.
    """
    try:
        # Get all parts currently in the list
        current_parts = get_part_list_parts(list_id)
        
        if not current_parts:
            return {'success': True, 'removed': 0, 'message': 'Part list was already empty'}
        
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            return {'success': False, 'message': 'Missing Rebrickable credentials'}
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        logger.info(f"Clearing {len(current_parts)} parts from part list {list_id} using optimized method")
        
        # Strategy 1: Try to delete and recreate the entire list (most efficient)
        try:
            # First, get the list details to recreate it
            list_url = f'https://rebrickable.com/api/v3/users/{user_token}/partlists/{list_id}/'
            list_response = make_rate_limited_request(list_url, headers, timeout=20)
            
            if list_response and list_response.status_code == 200:
                list_details = list_response.json()
                list_name = list_details.get('name', 'Brick_Manager-Missing_Parts')
                
                # Delete the entire list
                delete_response = make_rate_limited_request(list_url, headers, method='DELETE', timeout=20)
                
                if delete_response and delete_response.status_code == 204:
                    logger.info(f"Successfully deleted part list {list_id}, recreating as '{list_name}'")
                    
                    # Recreate the list with the same name
                    new_list_id = find_or_create_missing_parts_list(list_name)
                    
                    if new_list_id:
                        logger.info(f"Successfully recreated part list as ID {new_list_id}")
                        update_rate_limit_tracker(False)
                        
                        return {
                            'success': True,
                            'removed': len(current_parts),
                            'total_parts': len(current_parts),
                            'method': 'delete_and_recreate',
                            'new_list_id': new_list_id,
                            'message': f"Successfully cleared {len(current_parts)} parts by recreating list"
                        }
                    else:
                        logger.warning("Failed to recreate list after deletion, falling back to individual removal")
                else:
                    logger.info("List deletion not supported or failed, using individual part removal")
            else:
                logger.info("Could not get list details, using individual part removal")
                
        except Exception as e:
            logger.info(f"List recreation failed ({e}), using individual part removal")
        
        # Strategy 2: Fallback to individual part deletion
        removed_count = 0
        errors = []
        
        logger.info(f"Removing {len(current_parts)} parts individually from part list {list_id}")
        
        for i, part in enumerate(current_parts):
            if should_skip_api_calls():
                logger.warning(f"Stopping part removal at {i+1}/{len(current_parts)} due to rate limiting")
                break
            
            try:
                part_num = part['part']['part_num']
                color_id = part['color']['id']
                
                url = f'https://rebrickable.com/api/v3/users/{user_token}/partlists/{list_id}/parts/{part_num}/{color_id}/'
                
                response = make_rate_limited_request(url, headers, method='DELETE', timeout=20)
                
                if response and response.status_code == 204:
                    removed_count += 1
                    update_rate_limit_tracker(False)
                    
                    # Progress feedback for every 50 parts
                    if (i + 1) % 50 == 0:
                        logger.info(f"Removed {i + 1}/{len(current_parts)} parts")
                    
                elif response and response.status_code == 429:
                    logger.warning(f"Rate limited removing part {part_num}/{color_id} ({i+1}/{len(current_parts)})")
                    update_rate_limit_tracker(True)
                    # Continue trying with rate limiting delays
                else:
                    error_msg = f"Failed to remove {part_num}/{color_id}: {response.status_code if response else 'No response'}"
                    errors.append(error_msg)
                    logger.debug(error_msg)
                    
            except Exception as e:
                error_msg = f"Error removing part: {e}"
                errors.append(error_msg)
                logger.debug(error_msg)
                continue
        
        success = removed_count > 0 or len(current_parts) == 0
        
        result = {
            'success': success,
            'removed': removed_count,
            'total_parts': len(current_parts),
            'method': 'individual_deletion',
            'errors': errors
        }
        
        if success:
            result['message'] = f"Successfully removed {removed_count}/{len(current_parts)} parts from part list"
            if len(errors) > 0:
                result['message'] += f" ({len(errors)} parts had errors)"
        else:
            result['message'] = f"Failed to remove parts from part list. Errors: {'; '.join(errors[:3])}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error clearing part list: {e}")
        return {'success': False, 'message': f'Error clearing part list: {str(e)}'}


def find_inventory_part_ids_bulk(missing_parts):
    """
    Find inventory part IDs for multiple parts using bulk API operations.
    This dramatically reduces the number of API calls by using set-level queries
    instead of individual part lookups.
    
    Args:
        missing_parts: List of parts with part_num, color_id, and set_num
    
    Returns:
        List of parts with inv_part_id added for those that were found
    """
    if not missing_parts:
        return []
    
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            logger.error("Missing Rebrickable credentials for bulk inventory lookup")
            return []
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        # Group parts by set number for bulk processing
        parts_by_set = {}
        parts_with_ids = []
        
        for part in missing_parts:
            set_num = part.get('set_num')
            if set_num:
                if set_num not in parts_by_set:
                    parts_by_set[set_num] = []
                parts_by_set[set_num].append(part)
        
        logger.info(f"Processing {len(missing_parts)} parts across {len(parts_by_set)} sets using bulk API queries")
        
        # Process each set's parts in bulk
        for set_num, set_parts in parts_by_set.items():
            if should_skip_api_calls():
                logger.warning(f"Stopping bulk processing due to rate limiting")
                break
            
            try:
                # Get all parts for this set in one API call
                url = f'https://rebrickable.com/api/v3/lego/sets/{set_num}/parts/'
                params = {'page_size': 1000}  # Get all parts at once
                
                response = make_rate_limited_request(url, headers, params, timeout=30)
                
                if response and response.status_code == 200:
                    set_inventory = response.json()
                    inventory_parts = set_inventory.get('results', [])
                    
                    # Create lookup map for this set's parts
                    part_lookup = {}
                    for inv_part in inventory_parts:
                        part_num = inv_part['part']['part_num']
                        color_id = inv_part['color']['id']
                        key = f"{part_num}_{color_id}"
                        part_lookup[key] = inv_part['id']
                    
                    # Match our missing parts to inventory parts
                    matched_count = 0
                    for part in set_parts:
                        key = f"{part['part_num']}_{part['color_id']}"
                        if key in part_lookup:
                            part['inv_part_id'] = part_lookup[key]
                            parts_with_ids.append(part)
                            matched_count += 1
                    
                    logger.info(f"Set {set_num}: Found {matched_count}/{len(set_parts)} parts in inventory")
                    update_rate_limit_tracker(False)  # Success
                    
                elif response and response.status_code == 429:
                    logger.warning(f"Rate limited while processing set {set_num}")
                    update_rate_limit_tracker(True)  # Rate limited
                    break  # Stop processing on rate limit
                else:
                    logger.warning(f"Failed to get inventory for set {set_num}: {response.status_code if response else 'No response'}")
                    
            except Exception as e:
                logger.error(f"Error processing set {set_num}: {e}")
                continue
        
        logger.info(f"Bulk processing completed: {len(parts_with_ids)} parts found with inventory IDs")
        return parts_with_ids
        
    except Exception as e:
        logger.error(f"Error in bulk inventory lookup: {e}")
        return []


def remove_parts_from_part_list(list_id, parts_to_remove):
    """
    Remove specific parts from a part list.
    Each part should have part_num, color_id, and optionally list_part_id.
    """
    if not parts_to_remove:
        return {'success': True, 'removed': 0, 'message': 'No parts to remove'}
    
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            return {'success': False, 'message': 'Missing Rebrickable credentials'}
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        removed_count = 0
        errors = []
        
        logger.info(f"Removing {len(parts_to_remove)} specific parts from part list {list_id}")
        
        for i, part in enumerate(parts_to_remove):
            if should_skip_api_calls():
                logger.warning(f"Stopping part removal at {i+1}/{len(parts_to_remove)} due to rate limiting")
                break
            
            try:
                part_num = part['part_num']
                color_id = part['color_id']
                
                url = f'https://rebrickable.com/api/v3/users/{user_token}/partlists/{list_id}/parts/{part_num}/{color_id}/'
                
                response = make_rate_limited_request(url, headers, method='DELETE', timeout=20)
                
                if response and response.status_code == 204:
                    removed_count += 1
                    update_rate_limit_tracker(False)
                    
                    # Progress feedback for every 25 parts
                    if (i + 1) % 25 == 0:
                        logger.info(f"Removed {i + 1}/{len(parts_to_remove)} parts")
                    
                elif response and response.status_code == 429:
                    logger.warning(f"Rate limited removing part {part_num}/{color_id} ({i+1}/{len(parts_to_remove)})")
                    update_rate_limit_tracker(True)
                    # Continue trying with rate limiting delays
                else:
                    error_msg = f"Failed to remove {part_num}/{color_id}: {response.status_code if response else 'No response'}"
                    errors.append(error_msg)
                    logger.debug(error_msg)
                    
            except Exception as e:
                error_msg = f"Error removing part: {e}"
                errors.append(error_msg)
                logger.debug(error_msg)
                continue
        
        success = removed_count > 0 or len(parts_to_remove) == 0
        
        result = {
            'success': success,
            'removed': removed_count,
            'total_parts': len(parts_to_remove),
            'errors': errors
        }
        
        if success:
            result['message'] = f"Successfully removed {removed_count}/{len(parts_to_remove)} parts from part list"
            if len(errors) > 0:
                result['message'] += f" ({len(errors)} parts had errors)"
        else:
            result['message'] = f"Failed to remove parts from part list. Errors: {'; '.join(errors[:3])}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error removing parts from part list: {e}")
        return {'success': False, 'message': f'Error removing parts: {str(e)}'}


def update_part_quantities_in_list(list_id, parts_to_update):
    """
    Update quantities for existing parts in a part list.
    Since Rebrickable Part Lists API doesn't support direct quantity updates,
    we remove and re-add the parts with new quantities.
    """
    if not parts_to_update:
        return {'success': True, 'updated': 0, 'message': 'No parts to update'}
    
    try:
        logger.info(f"Updating quantities for {len(parts_to_update)} parts by removing and re-adding")
        
        # First, remove the parts with old quantities
        parts_to_remove = []
        for part in parts_to_update:
            parts_to_remove.append({
                'part_num': part['part_num'],
                'color_id': part['color_id']
            })
        
        remove_result = remove_parts_from_part_list(list_id, parts_to_remove)
        removed_count = remove_result.get('removed', 0)
        
        if removed_count == 0:
            return {
                'success': False,
                'updated': 0,
                'message': 'Failed to remove parts for quantity update'
            }
        
        # Then, add them back with new quantities
        parts_to_add = []
        for part in parts_to_update:
            parts_to_add.append({
                'part_num': part['part_num'],
                'color_id': part['color_id'],
                'missing_quantity': part['new_quantity']
            })
        
        add_result = add_parts_to_part_list(list_id, parts_to_add)
        added_count = add_result.get('added', 0)
        
        success = added_count > 0
        updated_count = min(removed_count, added_count)  # Only count successful remove+add pairs
        
        result = {
            'success': success,
            'updated': updated_count,
            'removed_for_update': removed_count,
            'added_back': added_count,
            'remove_result': remove_result,
            'add_result': add_result
        }
        
        if success:
            result['message'] = f"Successfully updated quantities for {updated_count} parts"
            if updated_count < len(parts_to_update):
                result['message'] += f" (some updates may have been rate limited)"
        else:
            result['message'] = "Failed to update part quantities"
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating part quantities: {e}")
        return {'success': False, 'message': f'Error updating quantities: {str(e)}'}


def sync_missing_parts_with_rebrickable(batch_size=None):
    """
    Synchronize missing parts from local database with Rebrickable's Part Lists feature using smart diff-based updates.
    
    This function:
    1. Gets all missing parts from the local database (excluding spare parts)
    2. Creates or finds 'Brick_Manager-Missing_Parts' part list
    3. Compares current list with local missing parts
    4. Only adds missing parts and removes/updates parts as needed
    
    Args:
        batch_size: Number of parts to process in one batch (default: 200 for collections >500, 100 otherwise)
    
    Returns:
        dict: Results of the synchronization operation
    """
    try:
        logger.info("Starting smart missing parts synchronization with Rebrickable Part Lists")
        
        # Get current missing parts from local database (excluding spare parts)
        local_missing = get_local_missing_parts(include_spare=False)
        
        # Find or create the missing parts list
        list_id = find_or_create_missing_parts_list("Brick_Manager-Missing_Parts")
        
        if not list_id:
            return {
                'success': False,
                'message': 'Failed to create or find missing parts list on Rebrickable'
            }
        
        # Get current parts in the Rebrickable list
        current_list_parts = get_part_list_parts(list_id)
        
        # Create lookup dictionaries for efficient comparison
        local_parts_dict = {}
        for part in local_missing:
            key = f"{part['part_num']}_{part['color_id']}"
            local_parts_dict[key] = part
        
        current_parts_dict = {}
        for part in current_list_parts:
            key = f"{part['part']['part_num']}_{part['color']['id']}"
            current_parts_dict[key] = {
                'part_num': part['part']['part_num'],
                'color_id': part['color']['id'],
                'quantity': part['quantity'],
                'list_part_id': part.get('id')  # For removal operations
            }
        
        # Smart diff analysis
        parts_to_add = []  # Parts in local but not in list
        parts_to_remove = []  # Parts in list but not in local
        parts_to_update = []  # Parts in both but with different quantities
        
        # Find parts to add (in local but not in list)
        for key, local_part in local_parts_dict.items():
            if key not in current_parts_dict:
                parts_to_add.append(local_part)
            else:
                # Check if quantity needs updating
                current_quantity = current_parts_dict[key]['quantity']
                if current_quantity != local_part['missing_quantity']:
                    parts_to_update.append({
                        'part_num': local_part['part_num'],
                        'color_id': local_part['color_id'],
                        'old_quantity': current_quantity,
                        'new_quantity': local_part['missing_quantity'],
                        'list_part_id': current_parts_dict[key]['list_part_id']
                    })
        
        # Find parts to remove (in list but not in local)
        for key, current_part in current_parts_dict.items():
            if key not in local_parts_dict:
                parts_to_remove.append(current_part)
        
        results = {
            'success': True,
            'summary': {
                'local_missing_count': len(local_missing),
                'list_parts_count': len(current_list_parts),
                'to_add': len(parts_to_add),
                'to_remove': len(parts_to_remove),
                'to_update': len(parts_to_update),
                'list_id': list_id
            },
            'operations': []
        }
        
        logger.info(f"Smart sync analysis: {len(parts_to_add)} to add, {len(parts_to_remove)} to remove, {len(parts_to_update)} to update")
        
        # Step 1: Remove parts that are no longer missing
        removed_count = 0
        if parts_to_remove:
            logger.info(f"Removing {len(parts_to_remove)} parts that are no longer missing")
            remove_result = remove_parts_from_part_list(list_id, parts_to_remove)
            removed_count = remove_result.get('removed', 0)
            results['operations'].append({
                'operation': 'remove_obsolete',
                'result': remove_result
            })
        
        # Step 2: Add new missing parts
        added_count = 0
        rate_limited_count = 0
        
        if parts_to_add:
            # Apply batch size limiting for large additions
            if batch_size is None:
                if len(parts_to_add) > 1000:
                    batch_size = 500
                elif len(parts_to_add) > 500:
                    batch_size = 200
                else:
                    batch_size = len(parts_to_add)  # Process all if small
            
            batch_size = min(batch_size, len(parts_to_add))
            sample_parts = parts_to_add[:batch_size]
            
            logger.info(f"Adding {len(sample_parts)} new missing parts (out of {len(parts_to_add)} total)")
            
            add_result = add_parts_to_part_list(list_id, sample_parts)
            added_count = add_result.get('added', 0)
            rate_limited_count = add_result.get('rate_limited_count', 0)
            results['operations'].append({
                'operation': 'add_new_missing',
                'result': add_result
            })
        
        # Step 3: Update quantities for existing parts (if supported by API)
        updated_count = 0
        if parts_to_update:
            logger.info(f"Found {len(parts_to_update)} parts with quantity changes")
            # Note: Rebrickable Part Lists API might not support direct quantity updates
            # We might need to remove and re-add these parts
            update_result = update_part_quantities_in_list(list_id, parts_to_update)
            updated_count = update_result.get('updated', 0)
            results['operations'].append({
                'operation': 'update_quantities',
                'result': update_result
            })
        
        logger.info(f"Smart sync completed - added {added_count}, removed {removed_count}, updated {updated_count} parts")
        
        results['summary']['actual_added'] = added_count
        results['summary']['actual_removed'] = removed_count
        results['summary']['actual_updated'] = updated_count
        results['summary']['rate_limited_count'] = rate_limited_count
        results['summary']['total_local'] = len(local_missing)
        results['summary']['sample_processed'] = len(parts_to_add) if batch_size and len(parts_to_add) > batch_size else len(parts_to_add)
        
        # Enhanced message with smart sync information
        message_parts = [
            f"Smart synchronization completed! ",
            f"Found {len(local_missing)} missing parts locally vs {len(current_list_parts)} in list. "
        ]
        
        if added_count > 0:
            message_parts.append(f"Added {added_count} new missing parts. ")
        if removed_count > 0:
            message_parts.append(f"Removed {removed_count} parts no longer missing. ")
        if updated_count > 0:
            message_parts.append(f"Updated quantities for {updated_count} parts. ")
        if added_count == 0 and removed_count == 0 and updated_count == 0:
            message_parts.append("No changes needed - lists are already in sync! ")
        
        if rate_limited_count > 0:
            message_parts.append(f"{rate_limited_count} operations were rate limited and will be completed in the next sync.")
        
        results['summary']['message'] = "".join(message_parts)
        
        return results
        
    except Exception as e:
        logger.error(f"Error during smart missing parts synchronization: {e}")
        return {
            'success': False,
            'message': f'Smart synchronization failed: {str(e)}'
        }