import requests
from config import Config


def get_part_details(part_num):
    print(f"Fetching part details for {part_num}")
    url = f'https://rebrickable.com/api/v3/lego/parts/{part_num}/'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch part details for {
              part_num}: {response.status_code}")
        return None


def get_category_name(part_cat_id):
    url = f'https://rebrickable.com/api/v3/lego/part_categories/{part_cat_id}/'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'key {Config.REBRICKABLE_TOKEN}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get('name', 'Unknown Category')
    else:
        print(f"Failed to fetch category name for {
              part_cat_id}: {response.status_code}")
        return 'Unknown Category'


def get_predictions(file_path, filename):
    api_url = "https://api.brickognize.com/predict/"
    headers = {'accept': 'application/json'}
    files = {'query_image': (filename, open(file_path, 'rb'), 'image/jpeg')}

    response = requests.post(api_url, headers=headers, files=files)

    try:
        return response.json()
    except ValueError:
        print("Error decoding JSON response from the API")
        return None
