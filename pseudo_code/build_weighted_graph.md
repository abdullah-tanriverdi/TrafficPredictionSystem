FUNCTION build_weighted_graph(traffic_segments, lat_min, lat_max, lon_min, lon_max) RETURNS DirectedGraph G

    INITIALIZE directed graph G

    FOR each traffic_segment in traffic_segments DO
        EXTRACT jam_factor from currentFlow.jamFactor (default 1.0)
        EXTRACT shape links containing point coordinates

        FOR each link in links DO
            FILTER points within bounding box (lat_min, lat_max, lon_min, lon_max)
            IF less than 2 points after filtering THEN CONTINUE

            FOR consecutive point pairs in filtered_points DO
                CALCULATE geodesic distance between points -> length_meters
                COMPUTE weight = length_meters * jam_factor

                ADD directed edge to G with:
                    - start point (lat, lon)
                    - end point (lat, lon)
                    - edge attribute: weight
                    - edge attribute: points (the two points as dicts)

    RETURN graph G
