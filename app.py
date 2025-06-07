from flask import Flask, render_template, request, redirect, url_for
import folium
from folium.plugins import HeatMap
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
HERE_API_KEY = os.getenv("HERE_API_KEY")

def geocode(input_str):
    try:
        # Eğer doğrudan koordinatsa (örnek: "41.0,29.0")
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
    except:
        return None, None
    return None, None

@app.route('/')
def index():
    m = folium.Map(location=[41.015, 28.9795], zoom_start=12)
    return render_template('index.html', map=m._repr_html_(), start='', end='')

@app.route('/generate_route', methods=['POST'])
def generate_route():
    start_input = request.form['start']
    end_input = request.form['end']

    start_lat, start_lon = geocode(start_input)
    end_lat, end_lon = geocode(end_input)

    if not all([start_lat, start_lon, end_lat, end_lon]):
        return redirect(url_for('index'))

    # Haritayı merkezle
    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    # Marker'lar
    folium.Marker([start_lat, start_lon], popup="Başlangıç", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_lat, end_lon], popup="Bitiş", icon=folium.Icon(color='red')).add_to(m)

    # Trafik verisi al
    bbox = f"{min(start_lon, end_lon)},{min(start_lat, end_lat)},{max(start_lon, end_lon)},{max(start_lat, end_lat)}"
    traffic_url = f"https://data.traffic.hereapi.com/v7/flow"
    params = {
        "in": f"bbox:{bbox}",
        "locationReferencing": "shape",
        "apiKey": HERE_API_KEY
    }
    response = requests.get(traffic_url, params=params)
    data = response.json()

    # Heatmap verileri
    heatmap_data = []
    if "results" in data:
        for result in data["results"]:
            links = result.get("location", {}).get("shape", {}).get("links", [])
            for link in links:
                density = link.get("trafficDensity", 0.5)
                for pt in link.get("points", []):
                    heatmap_data.append([pt['lat'], pt['lng'], density])

    if heatmap_data:
        HeatMap(heatmap_data, radius=25, blur=20, max_zoom=13).add_to(m)

    return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input)

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
