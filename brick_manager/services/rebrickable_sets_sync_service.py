"""
Rebrickable user sets synchronization service.

This service handles the synchronization of user sets with Rebrickable's Lists feature,
specifically creating and maintaining a "Brick_Manager" list.
"""

import logging
import requests
from models import db, User_Set
from services.token_service import get_rebrickable_user_token, get_rebrickable_api_key

logger = logging.getLogger(__name__)

def get_rebrickable_lists():
    """
    Get all lists for the authenticated user from Rebrickable.
    
    Returns:
        list: List of user lists from Rebrickable
    """
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            logger.error("Missing Rebrickable credentials")
            return []
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        url = f'https://rebrickable.com/api/v3/users/{user_token}/setlists/'
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        else:
            logger.error(f"Failed to get lists: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting Rebrickable lists: {e}")
        return []

def create_brick_manager_list():
    """
    Create the "Brick_Manager" list on Rebrickable.
    
    Returns:
        dict: Result of list creation with list ID if successful
    """
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            return {'success': False, 'message': 'Missing Rebrickable credentials'}
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}',
            'Content-Type': 'application/json'
        }
        
        list_data = {
            'name': 'Brick_Manager',
            'is_buildable': True
        }
        
        url = f'https://rebrickable.com/api/v3/users/{user_token}/setlists/'
        response = requests.post(url, json=list_data, headers=headers, timeout=20)
        
        if response.status_code == 201:
            created_list = response.json()
            logger.info(f"Created Brick_Manager list with ID: {created_list.get('id')}")
            return {
                'success': True,
                'list_id': created_list.get('id'),
                'message': 'Brick_Manager list created successfully'
            }
        else:
            logger.error(f"Failed to create list: {response.status_code} - {response.text}")
            return {
                'success': False,
                'message': f'Failed to create list: {response.text}'
            }
            
    except Exception as e:
        logger.error(f"Error creating Brick_Manager list: {e}")
        return {
            'success': False,
            'message': f'Error creating list: {str(e)}'
        }

def get_brick_manager_list():
    """
    Get the "Brick_Manager" list from Rebrickable, creating it if it doesn't exist.
    
    Returns:
        dict: Result with list information
    """
    try:
        # First, try to find existing Brick_Manager list
        lists = get_rebrickable_lists()
        brick_manager_list = None
        
        for list_item in lists:
            if list_item.get('name') == 'Brick_Manager':
                brick_manager_list = list_item
                break
        
        if brick_manager_list:
            logger.info(f"Found existing Brick_Manager list with ID: {brick_manager_list.get('id')}")
            return {
                'success': True,
                'list_id': brick_manager_list.get('id'),
                'message': 'Found existing Brick_Manager list',
                'created': False
            }
        else:
            # Create the list
            result = create_brick_manager_list()
            if result['success']:
                result['created'] = True
            return result
            
    except Exception as e:
        logger.error(f"Error getting Brick_Manager list: {e}")
        return {
            'success': False,
            'message': f'Error getting list: {str(e)}'
        }

def get_list_sets(list_id):
    """
    Get all sets in a specific Rebrickable list.
    
    Args:
        list_id: The ID of the list to query
        
    Returns:
        list: List of sets in the list
    """
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            logger.error("Missing Rebrickable credentials")
            return []
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        all_sets = []
        page = 1
        
        while True:
            url = f'https://rebrickable.com/api/v3/users/{user_token}/setlists/{list_id}/sets/'
            params = {'page': page, 'page_size': 100}
            
            response = requests.get(url, headers=headers, params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                all_sets.extend(results)
                
                if not data.get('next'):
                    break
                page += 1
            else:
                logger.error(f"Failed to get list sets: {response.status_code} - {response.text}")
                break
        
        return all_sets
        
    except Exception as e:
        logger.error(f"Error getting list sets: {e}")
        return []

def add_sets_to_list(list_id, set_data):
    """
    Add sets to a Rebrickable list using bulk operations.
    
    Args:
        list_id: The ID of the list
        set_data: Dictionary mapping set_num -> quantity, or list of set_nums (for backward compatibility)
        
    Returns:
        dict: Result of the operation
    """
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            return {'success': False, 'message': 'Missing Rebrickable credentials'}
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Handle both dictionary (set_num -> quantity) and list (set_nums) formats
        if isinstance(set_data, dict):
            sets_to_process = list(set_data.items())  # (set_num, quantity) pairs
        else:
            # Backward compatibility: treat as list of set numbers with quantity 1
            sets_to_process = [(set_num, 1) for set_num in set_data]
        
        if not sets_to_process:
            return {'success': True, 'added_count': 0, 'rate_limited_count': 0, 'message': 'No sets to add'}
        
        logger.info(f"Adding {len(sets_to_process)} sets to Rebrickable list using bulk API")
        
        # Try bulk addition first (most efficient)
        url = f'https://rebrickable.com/api/v3/users/{user_token}/setlists/{list_id}/sets/'
        
        # Prepare bulk data - API expects array of objects
        bulk_data = []
        for set_num, quantity in sets_to_process:
            bulk_data.append({
                'set_num': set_num,
                'quantity': quantity
            })
        
        try:
            # Try bulk addition
            response = requests.post(url, json=bulk_data, headers=headers, timeout=60)
            
            if response.status_code == 201:
                added_sets = response.json()
                added_count = len(added_sets) if isinstance(added_sets, list) else 1
                logger.info(f"Successfully added {added_count} sets to list via bulk operation")
                return {
                    'success': True,
                    'added_count': added_count,
                    'rate_limited_count': 0,
                    'total_attempted': len(sets_to_process),
                    'errors': [],
                    'message': f'Added {added_count}/{len(sets_to_process)} sets to list via bulk operation'
                }
            elif response.status_code == 429:
                # Bulk operation rate limited - fall back to individual requests
                logger.warning(f"Bulk set addition rate limited, falling back to individual requests for {len(sets_to_process)} sets")
                return add_sets_individually(list_id, sets_to_process, headers, user_token)
            else:
                logger.warning(f"Bulk set addition failed ({response.status_code}), falling back to individual requests: {response.text}")
                return add_sets_individually(list_id, sets_to_process, headers, user_token)
                
        except Exception as e:
            logger.warning(f"Bulk set addition error, falling back to individual requests: {e}")
            return add_sets_individually(list_id, sets_to_process, headers, user_token)
            
    except Exception as e:
        logger.error(f"Error adding sets to list: {e}")
        return {'success': False, 'message': f'Error adding sets: {str(e)}'}

def add_sets_individually(list_id, sets_to_process, headers, user_token):
    """
    Add sets individually when bulk operation fails or is rate limited.
    
    Args:
        list_id: The ID of the list
        sets_to_process: List of (set_num, quantity) tuples
        headers: HTTP headers for API requests
        user_token: Rebrickable user token
        
    Returns:
        dict: Result of the operation
    """
    added_count = 0
    errors = []
    rate_limited_count = 0
    
    for i, (set_num, quantity) in enumerate(sets_to_process):
        try:
            url = f'https://rebrickable.com/api/v3/users/{user_token}/setlists/{list_id}/sets/'
            data = {'set_num': set_num, 'quantity': quantity}
            
            response = requests.post(url, json=data, headers=headers, timeout=20)
            
            if response.status_code == 201:
                added_count += 1
                logger.debug(f"Added set {set_num} (qty: {quantity}) to list")
            elif response.status_code == 429:
                # Rate limited - this is expected for large sync operations
                rate_limited_count += 1
                logger.info(f"Rate limited on set {set_num} (attempt {i+1}/{len(sets_to_process)})")
                # Don't treat this as an error - just note it for summary
            else:
                error_msg = f"Failed to add {set_num} (qty: {quantity}): {response.text}"
                logger.warning(error_msg)
                errors.append(error_msg)
                
        except Exception as e:
            error_msg = f"Error adding {set_num}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    return {
        'success': True,
        'added_count': added_count,
        'rate_limited_count': rate_limited_count,
        'total_attempted': len(sets_to_process),
        'errors': errors,
        'message': f'Added {added_count}/{len(sets_to_process)} sets to list. {rate_limited_count} sets hit rate limits (will be retried on next sync).'
    }

def update_set_quantity_in_list(list_id, set_num, new_quantity):
    """
    Update the quantity of a specific set in a Rebrickable list.
    Since there's no direct update API, we need to remove and re-add the set.
    
    Args:
        list_id: The ID of the list
        set_num: The set number to update
        new_quantity: The new quantity
        
    Returns:
        dict: Result of the operation
    """
    try:
        user_token = get_rebrickable_user_token()
        api_key = get_rebrickable_api_key()
        
        if not user_token or not api_key:
            return {'success': False, 'message': 'Missing Rebrickable credentials'}
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}',
            'Content-Type': 'application/json'
        }
        
        # First, remove the set from the list
        delete_url = f'https://rebrickable.com/api/v3/users/{user_token}/setlists/{list_id}/sets/{set_num}/'
        delete_response = requests.delete(delete_url, headers=headers, timeout=20)
        
        if delete_response.status_code not in [204, 404]:  # 404 is okay if set wasn't in list
            logger.warning(f"Failed to remove set {set_num} for update: {delete_response.status_code} - {delete_response.text}")
            return {
                'success': False,
                'message': f'Failed to remove set {set_num} for quantity update: {delete_response.status_code}'
            }
        
        # Then add it back with the new quantity
        add_url = f'https://rebrickable.com/api/v3/users/{user_token}/setlists/{list_id}/sets/'
        add_data = {'set_num': set_num, 'quantity': new_quantity}
        add_response = requests.post(add_url, json=add_data, headers=headers, timeout=20)
        
        if add_response.status_code == 201:
            logger.debug(f"Updated set {set_num} quantity to {new_quantity}")
            return {
                'success': True,
                'updated_count': 1,
                'message': f'Updated {set_num} quantity to {new_quantity}'
            }
        elif add_response.status_code == 429:
            return {
                'success': False,
                'rate_limited': True,
                'message': f'Rate limited while updating {set_num}'
            }
        else:
            logger.error(f"Failed to add set {set_num} with new quantity: {add_response.status_code} - {add_response.text}")
            return {
                'success': False,
                'message': f'Failed to add set {set_num} with new quantity: {add_response.status_code}'
            }
            
    except Exception as e:
        logger.error(f"Error updating set quantity: {e}")
        return {'success': False, 'message': f'Error updating set quantity: {str(e)}'}

def remove_sets_from_list(list_id, set_nums):
    """
    Remove sets from a Rebrickable list.
    
    Args:
        list_id: The ID of the list
        set_nums: List of set numbers to remove
        
    Returns:
        dict: Result of the operation
    """
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
        
        for set_num in set_nums:
            try:
                url = f'https://rebrickable.com/api/v3/users/{user_token}/setlists/{list_id}/sets/{set_num}/'
                
                response = requests.delete(url, headers=headers, timeout=20)
                
                if response.status_code == 204:
                    removed_count += 1
                    logger.debug(f"Removed set {set_num} from list")
                else:
                    error_msg = f"Failed to remove {set_num}: {response.text}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error removing {set_num}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return {
            'success': True,
            'removed_count': removed_count,
            'total_attempted': len(set_nums),
            'errors': errors,
            'message': f'Removed {removed_count}/{len(set_nums)} sets from list'
        }
        
    except Exception as e:
        logger.error(f"Error removing sets from list: {e}")
        return {
            'success': False,
            'message': f'Error removing sets: {str(e)}'
        }

def sync_user_sets_with_rebrickable():
    """
    Synchronize local user sets with the Rebrickable "Brick_Manager" list.
    
    This function:
    1. Gets or creates the "Brick_Manager" list on Rebrickable
    2. Gets all local user sets
    3. Gets all sets currently in the Rebrickable list
    4. Adds new sets and removes sets no longer in local collection
    
    Returns:
        dict: Results of the synchronization operation
    """
    try:
        logger.info("Starting user sets synchronization with Rebrickable")
        
        # Step 1: Get or create the Brick_Manager list
        list_result = get_brick_manager_list()
        if not list_result['success']:
            return list_result
        
        list_id = list_result['list_id']
        logger.info(f"Using Brick_Manager list ID: {list_id}")
        
        # Step 2: Get all local user sets and count quantities
        local_sets = db.session.query(User_Set).all()
        local_set_quantities = {}  # Dictionary: set_num -> quantity
        
        for user_set in local_sets:
            if user_set.template_set and user_set.template_set.set_num:
                set_num = user_set.template_set.set_num
                local_set_quantities[set_num] = local_set_quantities.get(set_num, 0) + 1
        
        logger.info(f"Found {len(local_set_quantities)} unique local user sets with total quantity {sum(local_set_quantities.values())}")
        
        # Step 3: Get sets currently in the Rebrickable list with their quantities
        rebrickable_sets = get_list_sets(list_id)
        rebrickable_set_quantities = {}  # Dictionary: set_num -> quantity
        
        for rb_set in rebrickable_sets:
            if rb_set.get('set', {}).get('set_num'):
                set_num = rb_set['set']['set_num']
                quantity = rb_set.get('quantity', 1)  # Default to 1 if quantity not specified
                rebrickable_set_quantities[set_num] = quantity
        
        logger.info(f"Found {len(rebrickable_set_quantities)} sets in Rebrickable list with total quantity {sum(rebrickable_set_quantities.values())}")
        
        # Step 4: Calculate differences - sets that need to be added, removed, or updated
        local_set_nums = set(local_set_quantities.keys())
        rebrickable_set_nums = set(rebrickable_set_quantities.keys())
        
        sets_to_add = local_set_nums - rebrickable_set_nums  # Sets not in Rebrickable at all
        sets_to_remove = rebrickable_set_nums - local_set_nums  # Sets in Rebrickable but not local
        
        # Sets that exist in both but may have different quantities
        sets_to_update = []
        for set_num in local_set_nums & rebrickable_set_nums:
            local_qty = local_set_quantities[set_num]
            rebrickable_qty = rebrickable_set_quantities.get(set_num, 0)
            if local_qty != rebrickable_qty:
                sets_to_update.append((set_num, local_qty, rebrickable_qty))
        
        logger.info(f"Sets to add: {len(sets_to_add)}, Sets to remove: {len(sets_to_remove)}, Sets to update quantities: {len(sets_to_update)}")
        
        results = {
            'success': True,
            'summary': {
                'local_sets_count': len(local_set_quantities),
                'local_total_quantity': sum(local_set_quantities.values()),
                'rebrickable_sets_count': len(rebrickable_set_quantities),
                'rebrickable_total_quantity': sum(rebrickable_set_quantities.values()),
                'sets_to_add': len(sets_to_add),
                'sets_to_remove': len(sets_to_remove),
                'sets_to_update': len(sets_to_update),
                'list_created': list_result.get('created', False)
            },
            'operations': []
        }
        
        # Step 5: Add new sets with correct quantities
        if sets_to_add:
            # Create quantity dictionary for sets to add
            sets_to_add_with_qty = {set_num: local_set_quantities[set_num] for set_num in sets_to_add}
            add_result = add_sets_to_list(list_id, sets_to_add_with_qty)
            results['operations'].append({
                'operation': 'add_sets',
                'result': add_result
            })
            # Store add result for rate limiting info
            results['summary']['sets_to_add_result'] = add_result
        
        # Step 6: Update quantities for existing sets
        updated_count = 0
        update_rate_limited_count = 0
        if sets_to_update:
            for set_num, local_qty, rebrickable_qty in sets_to_update:
                update_result = update_set_quantity_in_list(list_id, set_num, local_qty)
                if update_result.get('success'):
                    updated_count += 1
                    logger.debug(f"Updated {set_num} quantity from {rebrickable_qty} to {local_qty}")
                elif update_result.get('rate_limited'):
                    update_rate_limited_count += 1
                    logger.info(f"Rate limited while updating {set_num} quantity")
                else:
                    logger.warning(f"Failed to update {set_num} quantity: {update_result.get('message')}")
            
            results['operations'].append({
                'operation': 'update_quantities',
                'result': {
                    'success': True,
                    'updated_count': updated_count,
                    'rate_limited_count': update_rate_limited_count,
                    'total_attempted': len(sets_to_update)
                }
            })
        
        # Step 7: Remove old sets
        if sets_to_remove:
            remove_result = remove_sets_from_list(list_id, list(sets_to_remove))
            results['operations'].append({
                'operation': 'remove_sets',
                'result': remove_result
            })
        
        # Calculate final counts
        total_added = sum(op['result'].get('added_count', 0) for op in results['operations'] if op['operation'] == 'add_sets')
        total_removed = sum(op['result'].get('removed_count', 0) for op in results['operations'] if op['operation'] == 'remove_sets')
        total_updated = sum(op['result'].get('updated_count', 0) for op in results['operations'] if op['operation'] == 'update_quantities')
        total_rate_limited = (
            sum(op['result'].get('rate_limited_count', 0) for op in results['operations'] if op['operation'] == 'add_sets') +
            sum(op['result'].get('rate_limited_count', 0) for op in results['operations'] if op['operation'] == 'update_quantities')
        )
        
        results['summary']['sets_added'] = total_added
        results['summary']['sets_removed'] = total_removed
        results['summary']['sets_updated'] = total_updated
        results['summary']['rate_limited_count'] = total_rate_limited
        
        # Enhanced message with quantity and rate limiting information
        message_parts = [
            f"Synchronization completed! ",
            f"List {'created' if list_result.get('created') else 'found'} successfully. ",
            f"Added {total_added} sets, updated {total_updated} quantities, removed {total_removed} sets."
        ]
        
        if total_rate_limited > 0:
            message_parts.append(f" {total_rate_limited} operations were rate limited and will be synced automatically in the next scheduled run.")
        
        message_parts.append(f" Total unique sets in local collection: {len(local_set_quantities)} (total quantity: {sum(local_set_quantities.values())})")
        
        results['summary']['message'] = "".join(message_parts)
        
        logger.info(f"User sets synchronization completed - added {total_added}, updated {total_updated}, removed {total_removed}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during user sets synchronization: {e}")
        return {
            'success': False,
            'message': f'User sets synchronization failed: {str(e)}'
        }