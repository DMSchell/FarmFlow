from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
import os
from backend.moisture_database import moisture_insert_data, moisture_import_from_csv
from backend.nutrients_database import nutrient_insert_data, nutrient_import_from_csv

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def fetch_moisture_data(sensor_id=None):
    conn = sqlite3.connect("soil_moisture.db")
    query = "SELECT sensor_id, moisture_level, timestamp, watering FROM moisture_data"
    if sensor_id:
        query += f" WHERE sensor_id = '{sensor_id}'"
    query += " ORDER BY sensor_id ASC, timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
def fetch_nutrient_data(sensor_id=None):
    conn = sqlite3.connect("soil_nutrients.db")
    query = "SELECT sensor_id, timestamp, nitrogen, phosphorus, potassium FROM nutrient_data"
    if sensor_id:
        query += f" WHERE sensor_id = '{sensor_id}'"
    query += " ORDER BY sensor_id ASC, timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" in request.files:
            file = request.files["file"]
            if file.filename.endswith(".csv"):
                file_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(file_path)
                moisture_import_from_csv(file_path)
        
        else:
            sensor_id = request.form["sensor_id"]
            moisture_level = request.form["moisture_level"]
            moisture_insert_data(sensor_id, float(moisture_level))

        return redirect("/")
    
    moisture_data = fetch_moisture_data()
    nutrient_data = fetch_nutrient_data()
    
    # error may occur if moisture and nutrient data have differently named sensors; figure out later
    sensors = moisture_data['sensor_id'].unique()

    return render_template("index.html", moisture_data=moisture_data, nutrient_data=nutrient_data, sensors=sensors)

@app.route("/sensor/<sensor_id>")
def sensor(sensor_id):
    moisture_data = fetch_moisture_data(sensor_id)
    moisture_data['timestamp'] = pd.to_datetime(moisture_data['timestamp'])
    moisture_data = moisture_data.sort_values(by='timestamp')
    nutrient_data = fetch_nutrient_data(sensor_id)
    nutrient_data['timestamp'] = pd.to_datetime(nutrient_data['timestamp'])
    nutrient_data = nutrient_data.sort_values(by='timestamp')

    moisture_graph = get_moisture_graph(sensor_id, moisture_data, 40)
    moisture_graph = moisture_graph.to_html(full_html=False)
    nutrient_graph = get_nutrient_graph(sensor_id, nutrient_data)
    nutrient_graph = nutrient_graph.to_html(full_html=False)

    return render_template("sensor.html", moisture_data=moisture_data, moisture_graph=moisture_graph, nutrient_data=nutrient_data, nutrient_graph=nutrient_graph, sensor_id=sensor_id)

@app.route("/upload_moisture", methods=["POST"])
def upload_moisture():
    file = request.files["moisture_file"]
    if file.filename.endswith(".csv"):
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        moisture_import_from_csv(file_path)
    return redirect("/")

@app.route("/upload_nutrients", methods=["POST"])
def upload_nutrients():
    file = request.files["nutrient_file"]
    if file.filename.endswith(".csv"):
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        nutrient_import_from_csv(file_path)
    return redirect("/")

@app.route("/update_graph", methods=["POST"])
def update_graph():
    sensor_id = request.form.get("sensor_id")
    moisture_goal = request.form.get("goal")

    try:
        moisture_goal = float(moisture_goal)
    except ValueError:
        return "Invalid goal", 400

    moisture_data = fetch_moisture_data(sensor_id)
    moisture_data['timestamp'] = pd.to_datetime(moisture_data['timestamp'])
    moisture_data = moisture_data.sort_values(by='timestamp')

    moisture_graph = get_moisture_graph(sensor_id, moisture_data, moisture_goal)
    moisture_graph = pio.to_json(moisture_graph)
    return moisture_graph

#moisture graph
def get_moisture_graph(sensor_id, moisture_data, moisture_goal):
    moisture_fig = go.Figure()
    moisture_fig.add_trace(go.Scatter(
        x=moisture_data['timestamp'],
        y=moisture_data['moisture_level'],
        mode='lines+markers',
        name='Moisture Level',
        line=dict(color='green')
    ))
    moisture_fig.add_shape(
        type="line",
        x0=moisture_data['timestamp'].min(),
        x1=moisture_data['timestamp'].max(),
        y0=moisture_goal,
        y1=moisture_goal,
        line=dict(color="gray", width=2, dash="dash"),
    )
    moisture_fig.add_annotation(
        x=moisture_data['timestamp'].min(),
        y=moisture_goal,
        text="Moisture Goal (40%)",
        showarrow=False,
        xanchor="right",
        font=dict(color="gray", size=12)
    )
    for i in range(len(moisture_data) - 1):
        if moisture_data.iloc[i]['watering'] == "1":
            moisture_fig.add_shape(
                type="rect",
                x0=moisture_data.iloc[i]['timestamp'],
                x1=moisture_data.iloc[i + 1]['timestamp'],
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                fillcolor="rgba(0, 100, 255, 0.2)",
                opacity=0.4,
                layer="below",
                line_width=0
            )
    moisture_fig.update_layout(
        title=f"Soil Moisture for Sensor {sensor_id}",
        xaxis_title="Time",
        yaxis_title="Moisture Level (%)",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
    )
    return moisture_fig

#nutrient graph
def get_nutrient_graph(sensor_id, nutrient_data):

    nutrient_fig = go.Figure()
    nutrient_fig.add_trace(go.Scatter(
        x=nutrient_data['timestamp'],
        y=nutrient_data['nitrogen'],
        mode='lines+markers',
        name='Nitrogen (N)',
        line=dict(color='blue')
    ))
    nutrient_fig.add_trace(go.Scatter(
        x=nutrient_data['timestamp'],
        y=nutrient_data['phosphorus'],
        mode='lines+markers',
        name='Phosphorus (P)',
        line=dict(color='orange')
    ))
    nutrient_fig.add_trace(go.Scatter(
        x=nutrient_data['timestamp'],
        y=nutrient_data['potassium'],
        mode='lines+markers',
        name='Potassium (K)',
        line=dict(color='red')
    ))
    nutrient_fig.update_layout(
        title=f"Soil Nutrient Content for Sensor {sensor_id}",
        xaxis_title="Time",
        yaxis_title="Nutrient Level (%)",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
    )
    return nutrient_fig

if __name__ == "__main__":
    app.run(debug=True)
