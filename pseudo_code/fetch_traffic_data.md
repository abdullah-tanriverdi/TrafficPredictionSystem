```pseudo
FUNCTION fetch_traffic_data(lat_min, lat_max, lon_min, lon_max) RETURNS traffic_segments OR None
    FORMAT bbox string as "lon_min,lat_min,lon_max,lat_max"

    SET API endpoint URL for HERE Traffic Flow API
    SET parameters:
        - in=bbox
        - locationReferencing=shape
        - apiKey=HERE_API_KEY

    SEND HTTP GET request to API endpoint with parameters
    IF response is successful THEN
        PARSE JSON and RETURN list of traffic segments (results)
    ELSE
        RETURN None
