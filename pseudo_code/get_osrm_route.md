```pseudo
FUNCTION get_osrm_route(start_coord, end_coord, duration_factor=1.4) RETURNS
    (route_coords, directions, total_distance_km, total_duration_min, average_speed)

    FORM OSRM API URL with start and end coordinates

    SET parameters:
        - overview=full
        - geometries=geojson
        - steps=true

    SEND HTTP GET request to OSRM API

    IF response not successful OR no routes THEN
        RETURN (None, None, None, None, None)

    PARSE first route:
        - EXTRACT route geometry coordinates
        - CONVERT geojson lon/lat pairs to lat/lon tuples

        - COMPUTE total_distance_km from route data
        - COMPUTE total_duration_min = route duration * duration_factor / 60
        - CALCULATE average_speed = total_distance_km / (total_duration_min / 60)

        - PARSE step-by-step directions with instruction text

    RETURN all parsed data
