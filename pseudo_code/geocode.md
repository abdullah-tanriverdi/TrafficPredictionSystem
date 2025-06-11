FUNCTION geocode(input_str) RETURNS (latitude, longitude) OR (None, None)
    IF input_str contains ',' THEN
        PARSE lat, lon from input string
        RETURN lat, lon
    ELSE
        CALL OpenStreetMap Nominatim API with input_str
        IF response successful AND results present THEN
            EXTRACT first result latitude and longitude
            RETURN lat, lon
    ON FAILURE OR EXCEPTION:
        RETURN None, None
