import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
HERE_API_KEY = os.getenv("HERE_API_KEY")

def geocode(address):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': address, 'format': 'json', 'limit': 1}
    headers = {'User-Agent': 'trafik-verisi-test'}
    response = requests.get(url, params=params, headers=headers)
    if response.ok and response.json():
        data = response.json()[0]
        return float(data['lat']), float(data['lon'])
    return None, None

def fetch_traffic_data(start_address, end_address):
    start_lat, start_lon = geocode(start_address)
    end_lat, end_lon = geocode(end_address)

    if not all([start_lat, start_lon, end_lat, end_lon]):
        print("Geocode başarısız.")
        return

    bbox = f"{min(start_lon, end_lon)},{min(start_lat, end_lat)},{max(start_lon, end_lon)},{max(start_lat, end_lat)}"
    url = f"https://data.traffic.hereapi.com/v7/flow?in=bbox:{bbox}&locationReferencing=shape&apiKey={HERE_API_KEY}"

    response = requests.get(url)
    if response.ok:
        traffic_data = response.json()
        with open('trafik_verisi.json', 'w', encoding='utf-8') as f:
            json.dump(traffic_data, f, indent=4, ensure_ascii=False)
        print("Trafik verisi 'trafik_verisi.json' dosyasına kaydedildi.")
    else:
        print("API isteği başarısız:", response.status_code)


if __name__ == '__main__':
    start = input("Başlangıç noktası: ")
    end = input("Bitiş noktası: ")
    fetch_traffic_data(start, end)
