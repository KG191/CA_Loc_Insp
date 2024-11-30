import requests
import csv
import math
import sys

API_KEY = 'AIzaSyDNdt-Um0cSjqNYQQBZwfdvdkHAUKMsqOI'
STREET_VIEW_URL = 'https://maps.googleapis.com/maps/api/streetview'
METADATA_URL = 'https://maps.googleapis.com/maps/api/streetview/metadata'

def get_panorama_metadata(lat, lon, view_type):
    params = {
        'location': f'{lat},{lon}',
        'key': API_KEY
    }

    # Remove the radius parameter to allow the API to find the nearest panorama
    # Remove or adjust the source parameter
    if view_type == 'FV':
        params['source'] = 'outdoor'  # Optionally set for footpath view
    # For RV, we can omit 'source' to include all panoramas

    response = requests.get(METADATA_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            return data
        else:
            print(f"No Street View available for location: {lat}, {lon}")
            return None
    else:
        print(f"Error fetching metadata: {response.status_code}")
        return None

def calculate_heading(pano_lat, pano_lon, target_lat, target_lon, view_type):
    """
    Calculates the heading from the panorama location to the target location.
    Applies adjustments based on the view type if necessary.
    """
    pano_lat_rad = math.radians(float(pano_lat))
    pano_lon_rad = math.radians(float(pano_lon))
    target_lat_rad = math.radians(float(target_lat))
    target_lon_rad = math.radians(float(target_lon))

    d_lon = target_lon_rad - pano_lon_rad
    x = math.sin(d_lon) * math.cos(target_lat_rad)
    y = math.cos(pano_lat_rad) * math.sin(target_lat_rad) - \
        math.sin(pano_lat_rad) * math.cos(target_lat_rad) * math.cos(d_lon)
    initial_heading = math.atan2(x, y)
    heading = (math.degrees(initial_heading) + 360) % 360

    # Apply adjustment for Footpath View if necessary
    if view_type == 'FV':
        # Example adjustment; you need to determine the correct value through testing
        adjustment_angle = 90  # Replace 0 with the desired adjustment angle
        heading = (heading + adjustment_angle) % 360

    return heading

def download_street_view_image(pano_id, heading, location_name):
    params = {
        'size': '640x640',
        'pano': pano_id,
        'heading': heading,
        'pitch': '0',
        'key': API_KEY
    }
    response = requests.get(STREET_VIEW_URL, params=params)
    if response.status_code == 200:
        with open(f'{location_name}.jpg', 'wb') as f:
            f.write(response.content)
        print(f'Image saved for location: {location_name}')
    else:
        print(f'Error fetching image for {location_name}: {response.status_code}')

def main():
    DEFAULT_VIEW_TYPE = 'RV'  # Default view type is Road View

    view_type = DEFAULT_VIEW_TYPE

    if len(sys.argv) > 1:
        view_type_input = sys.argv[1].upper()
        if view_type_input in ['RV', 'FV']:
            view_type = view_type_input
            print(f"Using user-specified view type: {view_type}")
        else:
            print("Invalid view type provided. Using default view type.")
    else:
        print(f"Using default view type: {view_type}")

    with open('Test1.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            target_lat = row['latitude']
            target_lon = row['longitude']
            location_name = f'location_{idx+1}'

            # Use original coordinates directly
            search_lat, search_lon = target_lat, target_lon

            metadata = get_panorama_metadata(search_lat, search_lon, view_type)
            if metadata:
                pano_id = metadata.get('pano_id')
                pano_location = metadata.get('location', {})
                pano_lat = pano_location.get('lat')
                pano_lon = pano_location.get('lng')
                if pano_lat and pano_lon:
                    heading = calculate_heading(pano_lat, pano_lon, target_lat, target_lon, view_type)
                    download_street_view_image(pano_id, heading, location_name)
                else:
                    print(f"Panorama location not available for {location_name}. Using default heading.")
                    download_street_view_image(pano_id, '0', location_name)
            else:
                print(f"Skipping location {location_name} due to missing metadata.")

if __name__ == '__main__':
    main()
