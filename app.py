from flask import Flask, render_template, request, redirect, url_for
import folium
import requests
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()  # .env dosyasını yükle

def geocode(address):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': address, 'format': 'json', 'limit': 1}
    headers = {'User-Agent': 'my-app'}
    response = requests.get(url, params=params, headers=headers)
    if response.ok and response.json():
        data = response.json()[0]
        return float(data['lat']), float(data['lon'])
    else:
        return None, None

def get_route_osrm(start_lon, start_lat, end_lon, end_lat):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {'overview': 'full', 'geometries': 'geojson'}
    response = requests.get(url, params=params)
    if response.ok:
        return response.json()
    return None

@app.route('/')
def index():
    m = folium.Map(location=[41.025, 29.016], zoom_start=13, tiles='OpenStreetMap')
    map_html = m._repr_html_()
    return render_template('index.html', map=map_html, start='', end='')

@app.route('/generate_route', methods=['POST'])
def generate_route():
    start = request.form['start']
    end = request.form['end']

    start_lat, start_lon = geocode(start)
    end_lat, end_lon = geocode(end)

    m = None

    if all([start_lat, start_lon, end_lat, end_lon]):
        route_data = get_route_osrm(start_lon, start_lat, end_lon, end_lat)
        if route_data and route_data.get('routes'):
            coords = route_data['routes'][0]['geometry']['coordinates']
            route_latlon = [(lat, lon) for lon, lat in coords]

            lats = [pt[0] for pt in route_latlon]
            lons = [pt[1] for pt in route_latlon]
            bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]

            m = folium.Map(tiles='OpenStreetMap')
            m.fit_bounds(bounds)

            folium.Marker(
                location=[start_lat, start_lon],
                popup=f'Başlangıç: {start}',
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)

            folium.Marker(
                location=[end_lat, end_lon],
                popup=f'Bitiş: {end}',
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)

            folium.PolyLine(
                locations=route_latlon,
                color='blue',
                weight=5,
                opacity=0.8
            ).add_to(m)

    if m is None:
        center = [41.025, 29.016]
        zoom = 13
        if all([start_lat, start_lon, end_lat, end_lon]):
            center = [(start_lat + end_lat) / 2, (start_lon + end_lon) / 2]
        elif start_lat and start_lon:
            center = [start_lat, start_lon]
        elif end_lat and end_lon:
            center = [end_lat, end_lon]

        m = folium.Map(location=center, zoom_start=zoom, tiles='OpenStreetMap')

        if start_lat and start_lon:
            folium.Marker(
                location=[start_lat, start_lon],
                popup=f'Başlangıç: {start}',
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)

        if end_lat and end_lon:
            folium.Marker(
                location=[end_lat, end_lon],
                popup=f'Bitiş: {end}',
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)

    map_html = m._repr_html_()
    return render_template('index.html', map=map_html, start=start, end=end)

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
