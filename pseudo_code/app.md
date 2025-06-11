START Flask Application

DEFINE route '/' AS index_page_handler
    INITIALIZE folium map centered at default coordinates (Istanbul)
    SET map tiles to Esri World Imagery
    RENDER 'index.html' WITH
        - empty start and end inputs
        - rendered base map
        - no errors

DEFINE route '/render_route' [POST] AS generate_route_handler
    READ user inputs: start_input, end_input

    CALL geocode(start_input) -> (start_lat, start_lon)
    CALL geocode(end_input) -> (end_lat, end_lon)

    IF any coordinate is missing THEN
        RENDER 'index.html' WITH error "Valid start and end points required"
        RETURN

    CALCULATE map center coordinates as midpoint of start and end

    INITIALIZE folium map centered at midpoint with Esri tiles

    ADD markers for start and end points on map

    DEFINE bounding box for traffic data with padding around start and end

    CALL fetch_traffic_data(bounding_box) -> initial_traffic_data
    IF traffic data is None THEN
        RENDER 'index.html' WITH error "Failed to fetch traffic data"
        RETURN

    CALL build_weighted_graph(initial_traffic_data, bounding_box) -> G
    CALL find_nearest_node(G, start_coordinates) -> start_node
    CALL find_nearest_node(G, end_coordinates) -> end_node

    IF start_node or end_node is None THEN
        RENDER 'index.html' WITH error "No suitable road near start or end point"
        RETURN

    CALL calculate_route(G, start_node, end_node) -> route_coords
    IF route_coords is None THEN
        RENDER 'index.html' WITH error "No valid route found"
        RETURN

    DRAW smart route on folium map as white polyline

    CALL get_osrm_route(start_coordinates, end_coordinates) -> (osrm_route, osrm_directions, osrm_total_length_km, osrm_total_time_min, osrm_average_speed)
    IF osrm_route exists THEN
        DRAW OSRM route on folium map as purple polyline
        CALL extract_street_names(osrm_directions) -> street_names
    ELSE
        street_names = empty list

    DEFINE extended bounding box covering both routes with small padding

    CALL fetch_traffic_data(extended_bbox) -> traffic_data_for_heatmap
    INITIALIZE heatmap_data as empty list
    INITIALIZE road_info list

    FOR each traffic segment IN traffic_data_for_heatmap DO
        EXTRACT jam_factor, speed, description
        APPEND {name, jam_factor, speed} to road_info

        FOR each coordinate point in segment shape DO
            IF point inside extended_bbox THEN
                APPEND (lat, lon, jam_factor) to heatmap_data

    IF heatmap_data not empty THEN
        ADD HeatMap layer on folium map

    DRAW bounding rectangle on folium map around extended_bbox

    COMPUTE total_length_meters by summing geodesic distances between consecutive route_coords points
    ASSUME average_speed_kmh = 30
    COMPUTE total_time_min = (total_length_m / 1000) / average_speed_kmh * 60

    RENDER 'index.html' with all collected data:
        - folium map
        - user inputs
        - start/end coordinates
        - route metrics
        - OSRM route info
        - street names
        - road traffic info
        - no error

END Flask Application
