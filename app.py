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
    m = folium.Map(location=[41.0603, 28.9870], zoom_start=14, tiles=None)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri World Imagery',
        overlay=False,
        control=False
    ).add_to(m)

    return render_template('index.html', map=m._repr_html_(), start='', end='', error=None,
                           start_coords=None, end_coords=None)

@app.route('/render_route', methods=['POST'])
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
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri World Imagery',
        overlay=False,
        control=False
    ).add_to(m)

    folium.Marker([start_lat, start_lon], popup="Başlangıç",
                  icon=folium.Icon(color='green', icon='play', prefix='fa')).add_to(m)
    folium.Marker([end_lat, end_lon], popup="Bitiş",
                  icon=folium.Icon(color='red', icon='stop', prefix='fa')).add_to(m)

    initial_padding = 0.03
    initial_lat_min = min(start_lat, end_lat) - initial_padding
    initial_lat_max = max(start_lat, end_lat) + initial_padding
    initial_lon_min = min(start_lon, end_lon) - initial_padding
    initial_lon_max = max(start_lon, end_lon) + initial_padding

    initial_traffic_data = fetch_traffic_data(initial_lat_min, initial_lat_max, initial_lon_min, initial_lon_max)
    if initial_traffic_data is None:
        error = "Trafik verisi alınırken hata oluştu."
        return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                               start_coords=(round(start_lat, 6), round(start_lon, 6)),
                               end_coords=(round(end_lat, 6), round(end_lon, 6)),
                               error=error)

    G = build_weighted_graph(initial_traffic_data, initial_lat_min, initial_lat_max, initial_lon_min, initial_lon_max)
    start_node = find_nearest_node(G, (start_lat, start_lon))
    end_node = find_nearest_node(G, (end_lat, end_lon))

    if not start_node or not end_node:
        error = "Başlangıç veya bitiş noktasına yakın uygun yol bulunamadı."
        return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                               start_coords=(round(start_lat, 6), round(start_lon, 6)),
                               end_coords=(round(end_lat, 6), round(end_lon, 6)),
                               error=error)

    route_coords = calculate_route(G, start_node, end_node)
    if route_coords is None:
        error = "Uygun rota bulunamadı."
        return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                               start_coords=(round(start_lat, 6), round(start_lon, 6)),
                               end_coords=(round(end_lat, 6), round(end_lon, 6)),
                               error=error)

    folium.PolyLine(route_coords, color="#FFFFFF", weight=8, opacity=1, tooltip="AKILLI ROTA", sticky=True).add_to(m)

    heatmap_data = []
    road_info = []

    osrm_route, osrm_directions, osrm_total_length_km, osrm_total_time_min, osrm_average_speed = get_osrm_route(
        (start_lat, start_lon), (end_lat, end_lon))
    street_names = []
    if osrm_route:
        folium.PolyLine(osrm_route, color="#800080", weight=8, opacity=1, tooltip="OSRM ROTA", sticky=True).add_to(m)
        street_names = extract_street_names(osrm_directions)

 
    all_lats = [coord[0] for coord in route_coords]
    all_lons = [coord[1] for coord in route_coords]

    if osrm_route:
        all_lats.extend([coord[0] for coord in osrm_route])
        all_lons.extend([coord[1] for coord in osrm_route])

    
    lat_min = min(all_lats) - 0.005
    lat_max = max(all_lats) + 0.005
    lon_min = min(all_lons) - 0.005
    lon_max = max(all_lons) + 0.005

    traffic_data = fetch_traffic_data(lat_min, lat_max, lon_min, lon_max)

    if traffic_data:
        for segment in traffic_data:
            location = segment.get("location", {})
            description = location.get("description", "Bilinmeyen Yol")
            current_flow = segment.get("currentFlow", {})
            jam_factor = current_flow.get("jamFactor", 0)
            speed = current_flow.get("speed", 0)

            road_info.append({
                "name": description,
                "jam_factor": jam_factor,
                "speed": round(speed, 2)
            })

            shape = location.get("shape", {})
            links = shape.get("links", [])
            for link in links:
                for pt in link.get("points", []):
                    lat = pt['lat']
                    lon = pt['lng']
                    if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                        heatmap_data.append([lat, lon, jam_factor])


    if heatmap_data:
        HeatMap(heatmap_data, radius=25, blur=20, max_zoom=14).add_to(m)
        all_lats.extend([pt[0] for pt in heatmap_data])
        all_lons.extend([pt[1] for pt in heatmap_data])

 
    lat_min = min(all_lats) - 0.005
    lat_max = max(all_lats) + 0.005
    lon_min = min(all_lons) - 0.005
    lon_max = max(all_lons) + 0.005

    folium.Rectangle(
        bounds=[[lat_min, lon_min], [lat_max, lon_max]],
        color='red', weight=3, fill=False
    ).add_to(m)

    # Diğer veriler
    turn_by_turn = get_turn_by_turn(route_coords)
    total_length_m = sum(geodesic(route_coords[i], route_coords[i + 1]).meters for i in range(len(route_coords) - 1))
    average_speed_kmh = 30
    total_time_min = round((total_length_m / 1000) / average_speed_kmh * 60, 1)

    return render_template('index.html', map=m._repr_html_(), start=start_input, end=end_input,
                           start_coords=(round(start_lat, 6), round(start_lon, 6)),
                           end_coords=(round(end_lat, 6), round(end_lon, 6)),
                           total_length_km=round(total_length_m),
                           total_time_min=total_time_min,
                           turn_by_turn=turn_by_turn,
                           osrm_directions=osrm_directions,
                           osrm_total_length_km=osrm_total_length_km,
                           osrm_total_time_min=osrm_total_time_min,
                           osrm_average_speed=osrm_average_speed,
                           street_names=street_names,
                           road_info=road_info,
                           error=None)

if __name__ == '__main__':
    app.run(debug=True)
