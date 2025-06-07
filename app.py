from flask import Flask, render_template, request, redirect, url_for
import folium
from folium.plugins import HeatMap
import requests
import os
from dotenv import load_dotenv
import networkx as nx
from geopy.distance import geodesic

app = Flask(__name__)
load_dotenv()
HERE_API_KEY = os.getenv("HERE_API_KEY")

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
    except:
        pass
    return None, None

def build_weighted_graph(traffic_results, lat_min, lat_max, lon_min, lon_max):
    G = nx.DiGraph()
    for segment in traffic_results:
        current_flow = segment.get("currentFlow", {})
        jam_factor = current_flow.get("jamFactor", 1.0)
        location = segment.get("location", {})
        shape = location.get("shape", {})
        links = shape.get("links", [])

        for link in links:
            points = link.get("points", [])
            if len(points) < 2:
                continue
            filtered_points = [pt for pt in points if lat_min <= pt['lat'] <= lat_max and lon_min <= pt['lng'] <= lon_max]
            if len(filtered_points) < 2:
                continue
            for i in range(len(filtered_points) - 1):
                start = (filtered_points[i]['lat'], filtered_points[i]['lng'])
                end = (filtered_points[i+1]['lat'], filtered_points[i+1]['lng'])
                length_m = geodesic(start, end).meters
                weight = length_m * jam_factor
                G.add_edge(start, end, weight=weight, points=[filtered_points[i], filtered_points[i+1]])
    return G

def find_nearest_node(G, point, max_distance=500):
    nearest = None
    min_dist = float('inf')
    for node in G.nodes:
        dist = geodesic(node, point).meters
        if dist < min_dist and dist <= max_distance:
            min_dist = dist
            nearest = node
    return nearest

@app.route('/')
def index():
    m = folium.Map(location=[41.015, 28.9795], zoom_start=12)
    return render_template('index.html', map=m._repr_html_(), start='', end='', error=None,
                           start_lat=None, start_lon=None, end_lat=None, end_lon=None)

@app.route('/generate_route', methods=['POST'])
def generate_route():
    start_input = request.form['start']
    end_input = request.form['end']

    start_lat, start_lon = geocode(start_input)
    end_lat, end_lon = geocode(end_input)

    if not all([start_lat, start_lon, end_lat, end_lon]):
        error = "Geçerli başlangıç ve bitiş noktaları giriniz."
        return render_template('index.html', map=None, start=start_input, end=end_input,
                               start_lat=None, start_lon=None, end_lat=None, end_lon=None,
                               error=error)

    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    folium.Marker([start_lat, start_lon], popup="Başlangıç", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_lat, end_lon], popup="Bitiş", icon=folium.Icon(color='red')).add_to(m)

    padding = 0.02  

    points = [
        (start_lat, start_lon),
        ((2*start_lat + end_lat)/3, (2*start_lon + end_lon)/3),
        ((start_lat + 2*end_lat)/3, (start_lon + 2*end_lon)/3),
        (end_lat, end_lon)
    ]

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]

    lat_min = min(lats) - padding
    lat_max = max(lats) + padding
    lon_min = min(lons) - padding
    lon_max = max(lons) + padding

    bbox = f"{lon_min},{lat_min},{lon_max},{lat_max}"

    traffic_url = "https://data.traffic.hereapi.com/v7/flow"
    params = {
        "in": f"bbox:{bbox}",
        "locationReferencing": "shape",
        "apiKey": HERE_API_KEY
    }
    response = requests.get(traffic_url, params=params)
    if not response.ok:
        error = "Trafik verisi alınırken hata oluştu."
        return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                               start_lat=round(start_lat,6), start_lon=round(start_lon,6),
                               end_lat=round(end_lat,6), end_lon=round(end_lon,6),
                               error=error)

    data = response.json()
    traffic_data = data.get("results", [])

    heatmap_data = []
    for segment in traffic_data:
        location = segment.get("location", {})
        shape = location.get("shape", {})
        links = shape.get("links", [])
        current_flow = segment.get("currentFlow", {})
        jam_factor = current_flow.get("jamFactor", 1.0)
        for link in links:
            points = link.get("points", [])
            for pt in points:
                if lat_min <= pt['lat'] <= lat_max and lon_min <= pt['lng'] <= lon_max:
                    heatmap_data.append([pt['lat'], pt['lng'], jam_factor])

    if heatmap_data:
        HeatMap(heatmap_data, radius=25, blur=20, max_zoom=14).add_to(m)

    folium.Rectangle(
        bounds=[[lat_min, lon_min], [lat_max, lon_max]],
        color='red', fill=False, weight=2
    ).add_to(m)

    G = build_weighted_graph(traffic_data, lat_min, lat_max, lon_min, lon_max)

    start_node = find_nearest_node(G, (start_lat, start_lon))
    end_node = find_nearest_node(G, (end_lat, end_lon))

    if not start_node or not end_node:
        error = "Başlangıç veya bitiş noktasına yakın uygun yol bulunamadı."
        return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                               start_lat=round(start_lat,6), start_lon=round(start_lon,6),
                               end_lat=round(end_lat,6), end_lon=round(end_lon,6),
                               error=error)

    try:
        path_nodes = nx.dijkstra_path(G, start_node, end_node, weight='weight')
    except nx.NetworkXNoPath:
        error = "Uygun rota bulunamadı."
        return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                               start_lat=round(start_lat,6), start_lon=round(start_lon,6),
                               end_lat=round(end_lat,6), end_lon=round(end_lon,6),
                               error=error)

    route_coords = []
    for i in range(len(path_nodes) - 1):
        edge_data = G.get_edge_data(path_nodes[i], path_nodes[i+1])
        if edge_data and 'points' in edge_data:
            route_coords.extend([(pt['lat'], pt['lng']) for pt in edge_data['points']])
        else:
            route_coords.append(path_nodes[i])
    route_coords.append(path_nodes[-1])

    folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

    return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                           start_lat=round(start_lat,6), start_lon=round(start_lon,6),
                           end_lat=round(end_lat,6), end_lon=round(end_lon,6),
                           error=None)

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
