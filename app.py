from flask import Flask, render_template, request
import folium

app = Flask(__name__)

@app.route('/')
def index():
    m = folium.Map(
        location=[41.025, 29.016],  
        zoom_start=13,
        tiles=None
    )

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri World Imagery',
        overlay=False,
        control=False
    ).add_to(m)

    map_html = m._repr_html_()
    return render_template('index.html', map=map_html)

@app.route('/generate_route', methods=['POST'])
def generate_route():
   
    start = request.form['start']
    end = request.form['end']

    m = folium.Map(
        location=[41.025, 29.016],
        zoom_start=15,
        tiles=None
    )

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri World Imagery',
        overlay=False,
        control=False
    ).add_to(m)


    start_coords = [41.0053, 29.0230]
    end_coords = [41.0438, 29.0094]

    folium.Marker(start_coords, popup="Başlangıç (Kadıköy)").add_to(m)
    folium.Marker(end_coords, popup="Bitiş (Beşiktaş)").add_to(m)

    map_html = m._repr_html_()
    return render_template('index.html', map=map_html)

if __name__ == '__main__':
    app.run(debug=True)
