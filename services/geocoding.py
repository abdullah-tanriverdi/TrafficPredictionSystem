import requests

def geocode(input_str):
    try:
        if ',' in input_str:
            lat, lon = map(float, input_str.split(','))
            return lat, lon
        else:
            url = 'https://nominatim.openstreetmap.org/search'
            params = {'q': input_str, 'format': 'json', 'limit': 1}
            headers = {'User-Agent': 'traffic-app'}
            response = requests.get(url, params=params, headers=headers)
            if response.ok and response.json():
                data = response.json()[0]
                return float(data['lat']), float(data['lon'])
    except Exception as e:
        print(f"Geocode error: {e}")
    return None, None
