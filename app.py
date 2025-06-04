from flask import Flask, render_template, request, redirect, url_for
import folium
from folium.plugins import HeatMap
import requests
import os
from dotenv import load_dotenv
import math

app = Flask(__name__)
load_dotenv()
HERE_API_KEY = os.getenv("HERE_API_KEY")

def geocode(address):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': address, 'format': 'json', 'limit': 1}
    headers = {'User-Agent': 'my-app'}
    response = requests.get(url, params=params, headers=headers)
    if response.ok and response.json():
        data = response.json()[0]
        return float(data['lat']), float(data['lon'])
    return None, None

def get_route_osrm(start_lon, start_lat, end_lon, end_lat):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {'overview': 'full', 'geometries': 'geojson'}
    response = requests.get(url, params=params)
    if response.ok:
        return response.json()
    return None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def is_point_near_route(point_lat, point_lon, route_coords, threshold=100):
    for r_lat, r_lon in route_coords:
        if haversine(point_lat, point_lon, r_lat, r_lon) <= threshold:
            return True
    return False

@app.route('/')
def index():
    m = folium.Map(location=[41.015137, 28.979530], zoom_start=12)
    return render_template('index.html', map=m._repr_html_(), start='', end='')

@app.route('/generate_route', methods=['POST'])
def generate_route():
    start = request.form['start']
    end = request.form['end']

    start_lat, start_lon = geocode(start)
    end_lat, end_lon = geocode(end)

    if not all([start_lat, start_lon, end_lat, end_lon]):
        return redirect(url_for('index'))

    route_data = get_route_osrm(start_lon, start_lat, end_lon, end_lat)
    m = folium.Map(tiles='cartodbpositron')

    if route_data and route_data.get('routes'):
        coords = route_data['routes'][0]['geometry']['coordinates']
        route_latlon = [(lat, lon) for lon, lat in coords]

        lats = [pt[0] for pt in route_latlon]
        lons = [pt[1] for pt in route_latlon]
        bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
        m.fit_bounds(bounds)

        folium.PolyLine(route_latlon, color='#1f77b4', weight=8, opacity=0.9).add_to(m)
        folium.Marker([start_lat, start_lon], popup='Başlangıç', icon=folium.Icon(color='green')).add_to(m)
        folium.Marker([end_lat, end_lon], popup='Bitiş', icon=folium.Icon(color='red')).add_to(m)

        bbox = f"{min(lons)},{min(lats)},{max(lons)},{max(lats)}"
        traffic_url = f"https://data.traffic.hereapi.com/v7/flow?in=bbox:{bbox}&locationReferencing=shape&apiKey={HERE_API_KEY}"
        response = requests.get(traffic_url)
        traffic_data = response.json()

        heatmap_data = []
        if 'results' in traffic_data:
            for result in traffic_data['results']:
                shape = result.get('location', {}).get('shape', {}).get('links', [])
                for link in shape:
                    density = link.get('trafficDensity', 1.0)
                    for point in link.get('points', []):
                        heatmap_data.append((point['lat'], point['lng'], density))

        filtered_heatmap_data = []
        for lat, lon, density in heatmap_data:
            if is_point_near_route(lat, lon, route_latlon, threshold=100) and density >= 0.15:
                filtered_heatmap_data.append((lat, lon, density))

        if filtered_heatmap_data:
            max_density = max(d[2] for d in filtered_heatmap_data)
           
            normalized_data = [(lat, lon, dens / max_density) for lat, lon, dens in filtered_heatmap_data]

            
            HeatMap(
                normalized_data,
                radius=25,
                blur=30,
                min_opacity=0.8,
                max_zoom=16,
                gradient={
                    0.0: 'green',
                    0.4: 'yellow',
                    0.7: 'orange',
                    1.0: 'red'
                }
            ).add_to(m)

    return render_template('index.html', map=m._repr_html_(), start=start, end=end)

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
