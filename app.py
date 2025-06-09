from flask import Flask, render_template, request
import folium
from folium.plugins import HeatMap
from services.geocoding import geocode
from services.traffic import fetch_traffic_data, build_weighted_graph, find_nearest_node
from services.routing import calculate_route, get_turn_by_turn, get_osrm_route
from geopy.distance import geodesic
from services.routing import extract_street_names

app = Flask(__name__)

@app.route('/')
def index():
    m = folium.Map(location=[41.015, 28.9795], zoom_start=12)
    return render_template('index.html', map=m._repr_html_(), start='', end='', error=None,
                           start_coords=None, end_coords=None)

@app.route('/generate_route', methods=['POST'])
def generate_route():
    start_input = request.form['start']
    end_input = request.form['end']

    start_lat, start_lon = geocode(start_input)
    end_lat, end_lon = geocode(end_input)

    if not all([start_lat, start_lon, end_lat, end_lon]):
        error = "Geçerli başlangıç ve bitiş noktaları giriniz."
        return render_template('index.html', map=None, start=start_input, end=end_input,
                               start_coords=None, end_coords=None,
                               error=error)

    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

    folium.Marker([start_lat, start_lon], popup="Başlangıç", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_lat, end_lon], popup="Bitiş", icon=folium.Icon(color='red')).add_to(m)

    padding = 0.02  
    lats = [start_lat, end_lat]
    lons = [start_lon, end_lon]
    lat_min = min(lats) - padding
    lat_max = max(lats) + padding
    lon_min = min(lons) - padding
    lon_max = max(lons) + padding

    traffic_data = fetch_traffic_data(lat_min, lat_max, lon_min, lon_max)
    if traffic_data is None:
        error = "Trafik verisi alınırken hata oluştu."
        return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                               start_coords=(round(start_lat,6), round(start_lon,6)),
                               end_coords=(round(end_lat,6), round(end_lon,6)),
                               error=error)

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

    G = build_weighted_graph(traffic_data, lat_min, lat_max, lon_min, lon_max)
    start_node = find_nearest_node(G, (start_lat, start_lon))
    end_node = find_nearest_node(G, (end_lat, end_lon))

    if not start_node or not end_node:
        error = "Başlangıç veya bitiş noktasına yakın uygun yol bulunamadı."
        return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                               start_coords=(round(start_lat,6), round(start_lon,6)),
                               end_coords=(round(end_lat,6), round(end_lon,6)),
                               error=error)

    route_coords = calculate_route(G, start_node, end_node)
    if route_coords is None:
        error = "Uygun rota bulunamadı."
        return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                               start_coords=(round(start_lat,6), round(start_lon,6)),
                               end_coords=(round(end_lat,6), round(end_lon,6)),
                               error=error)

    folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)
    turn_by_turn = get_turn_by_turn(route_coords)

    total_length_m = sum(geodesic(route_coords[i], route_coords[i+1]).meters for i in range(len(route_coords)-1))
    average_speed_kmh = 30
    total_time_min = round((total_length_m / 1000) / average_speed_kmh * 60, 1)

    osrm_route, osrm_directions, osrm_total_length_km, osrm_total_time_min, osrm_average_speed = get_osrm_route((start_lat, start_lon), (end_lat, end_lon))
    if osrm_route:
        folium.PolyLine(osrm_route, color="red", weight=4, opacity=0.7, tooltip="OSRM Rotası").add_to(m)
        street_names = extract_street_names(osrm_directions)
    else:
        osrm_directions = None
        osrm_total_length_km = None
        osrm_total_time_min = None
        osrm_average_speed = None
        street_names = []

    return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                           start_coords=(round(start_lat,6), round(start_lon,6)),
                           end_coords=(round(end_lat,6), round(end_lon,6)),
                           total_length_km=round(total_length_m / 1000, 2),
                           total_time_min=total_time_min,
                           turn_by_turn=turn_by_turn,
                           osrm_directions=osrm_directions,
                           osrm_total_length_km=osrm_total_length_km,
                           osrm_total_time_min=osrm_total_time_min,
                           osrm_average_speed=osrm_average_speed,
                           street_names=street_names,
                           error=None)


if __name__ == '__main__':
    app.run(debug=True)
