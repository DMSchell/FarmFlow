from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
import os
from backend.moisture_database import moisture_insert_data, moisture_import_from_csv
from backend.nutrients_database import nutrient_insert_data, nutrient_import_from_csv
from scripts.weather import fetch_weather_data
from datetime import datetime, timedelta
from scripts.prediction import predict_moisture, predict_nutrients

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
    query = "SELECT sensor_id, timestamp, nitrogen, phosphorus, potassium, fertilized FROM nutrient_data"
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
    
    sensors = moisture_data['sensor_id'].unique()

    return render_template("index.html", moisture_data=moisture_data, nutrient_data=nutrient_data, sensors=sensors)

@app.route("/sensor/<sensor_id>")
def sensor(sensor_id):
    # moisture
    moisture_data = fetch_moisture_data(sensor_id)
    moisture_data['timestamp'] = pd.to_datetime(moisture_data['timestamp'])
    moisture_data = moisture_data.sort_values(by='timestamp')
    moisture_graph = get_moisture_graph(sensor_id, moisture_data, 40)
    moisture_graph = moisture_graph.to_html(full_html=False)

    # nutrients
    nutrient_data = fetch_nutrient_data(sensor_id)
    nutrient_data['timestamp'] = pd.to_datetime(nutrient_data['timestamp'])
    nutrient_data = nutrient_data.sort_values(by='timestamp')
    nutrient_graph = get_nutrient_graph(sensor_id, nutrient_data, 50, 15, 150)
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

@app.route("/update_moisture_graph", methods=["POST"])
def update_moisture_graph():
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

@app.route("/update_nutrient_graph", methods=["POST"])
def update_nutrient_graph():
    sensor_id = request.form.get("sensor_id")
    nitrogen_goal = request.form.get("nitrogen_goal")
    phosphorus_goal = request.form.get("phosphorus_goal")
    potassium_goal = request.form.get("potassium_goal")

    try:
        nitrogen_goal = float(nitrogen_goal)
        phosphorus_goal = float(phosphorus_goal)
        potassium_goal = float(potassium_goal)
    except ValueError:
        return "Invalid goal", 400
    
    nutrient_data = fetch_nutrient_data(sensor_id)
    nutrient_data['timestamp'] = pd.to_datetime(nutrient_data['timestamp'])
    nutrient_data = nutrient_data.sort_values(by='timestamp')

    nutrient_graph = get_nutrient_graph(sensor_id, nutrient_data, nitrogen_goal, phosphorus_goal, potassium_goal)
    nutrient_graph = pio.to_json(nutrient_graph)
    return nutrient_graph
    


#moisture graph
def get_moisture_graph(sensor_id, moisture_data, moisture_goal):
    moisture_fig = go.Figure()
    # weather
    weather_start_date = moisture_data["timestamp"].min().strftime("%Y-%m-%d")
    weather_end_date = (moisture_data["timestamp"].max() + timedelta(days=7)).strftime("%Y-%m-%d")
    latitude, longitude = 40.7, -74.0
    weather_data = fetch_weather_data(latitude, longitude, weather_start_date, weather_end_date)
    moisture_fig.add_trace(go.Scatter(
        x=weather_data['timestamp'],
        y=weather_data['temperature_f'],
        mode='lines+markers',
        name='temperature (F)',
        line=dict(color='lightblue')
    ))
    moisture_fig.add_trace(go.Scatter(
        x=weather_data['timestamp'],
        y=weather_data['precipitation'],
        mode='lines+markers',
        name='precipitation',
        line=dict(color='blue')
    ))
    moisture_fig.add_trace(go.Scatter(
        x=weather_data['timestamp'],
        y=weather_data['humidity'],
        mode='lines+markers',
        name='humidity',
        line=dict(color='snow')
    ))
    # base moisture
    moisture_fig.add_shape(
        type="line",
        x0=moisture_data['timestamp'].min(),
        x1=(moisture_data["timestamp"].max() + timedelta(days=8)).strftime("%Y-%m-%d"),
        y0=moisture_goal,
        y1=moisture_goal,
        line=dict(color="gray", width=2, dash="dash"),
    )
    moisture_fig.add_annotation(
        x=moisture_data['timestamp'].min(),
        y=moisture_goal,
        text="Moisture Goal ("+str(moisture_goal)+"%)",
        showarrow=False,
        xanchor="right",
        font=dict(color="gray", size=12)
    )
    for i in range(len(moisture_data) - 1):
        if moisture_data.iloc[i]['watering'] == "1":
            moisture_fig.add_shape(
                type="rect",
                x0=moisture_data.iloc[i - 1]['timestamp'],
                x1=moisture_data.iloc[i]['timestamp'],
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                fillcolor="rgba(0, 100, 255, 0.2)",
                opacity=0.4,
                layer="below",
                line_width=0
            )
    moisture_fig.add_trace(go.Scatter(
        x=moisture_data['timestamp'],
        y=moisture_data['moisture_level'],
        mode='lines+markers',
        name='Moisture Level',
        line=dict(color='green')
    ))
    #prediction
    moisture_fig.add_shape(
        type="line",
        x0=moisture_data["timestamp"].max(),
        x1=moisture_data["timestamp"].max(),
        y0=0,
        y1=100,
        line=dict(color="blue", width=2, dash="dash")
    )
    moisture_fig.add_annotation(
        x=moisture_data["timestamp"].max(),
        y=100,
        text="Prediction line",
        font=dict(color="blue", size=12)
    )
    predicted_moisture_levels, predicted_watering_days = predict_moisture(moisture_data, moisture_goal)
    start_timestamp = moisture_data["timestamp"].max().strftime("%Y-%m-%d")
    future_timestamps = pd.date_range(start=start_timestamp, periods=9, freq='D')
    moisture_fig.add_trace(go.Scatter(
        x=future_timestamps,
        y=predicted_moisture_levels,
        mode='lines+markers',
        name='Future Predicted Moisture',
        line=dict(color='orange')
    ))
    start_date = datetime(2025, 3, 12)
    for i in range(len(predicted_watering_days) - 1):
        if predicted_watering_days[i] == "1":
            moisture_fig.add_shape(
                type="rect",
                x0=start_date + timedelta(days=i),
                x1=start_date + timedelta(days=i+1),
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                fillcolor="rgba(0, 100, 255, 0.2)",
                opacity=0.4,
                layer="below",
                line_width=0
            )

    #final
    moisture_fig.update_layout(
        title=f"Soil Moisture for Sensor {sensor_id}",
        xaxis_title="Time",
        yaxis_title="Moisture Level (%)",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
    )
    return moisture_fig

#nutrient graph
def get_nutrient_graph(sensor_id, nutrient_data, nitrogen_goal, phosphorus_goal, potassium_goal):
    nutrient_fig = go.Figure()
    #fertilizing
    for i in range(len(nutrient_data) - 1):
        if nutrient_data.iloc[i]['fertilized'] == "1":
            nutrient_fig.add_shape(
                type="line",
                x0=nutrient_data.iloc[i-1]['timestamp'],
                x1=nutrient_data.iloc[i-1]['timestamp'],
                y0=0,
                y1=175,
                line=dict(color="green", width=2, dash="dash")
            )
    #nitrogen
    nutrient_fig.add_shape(
        type="line",
        x0=nutrient_data['timestamp'].min(),
        x1=(nutrient_data["timestamp"].max() + timedelta(days=8)).strftime("%Y-%m-%d"),
        y0=nitrogen_goal,
        y1=nitrogen_goal,
        line=dict(color="blue", width=2, dash="dash"),
    )
    nutrient_fig.add_annotation(
        x=nutrient_data['timestamp'].min(),
        y=nitrogen_goal,
        text="Nitrogen Goal ("+str(nitrogen_goal)+" ppm)",
        showarrow=False,
        xanchor="right",
        font=dict(color="blue", size=12)
    )
    nutrient_fig.add_trace(go.Scatter(
        x=nutrient_data['timestamp'],
        y=nutrient_data['nitrogen'],
        mode='lines+markers',
        name='Nitrogen (N)',
        line=dict(color='blue')
    ))
    #phosphorus
    nutrient_fig.add_shape(
        type="line",
        x0=nutrient_data['timestamp'].min(),
        x1=(nutrient_data["timestamp"].max() + timedelta(days=8)).strftime("%Y-%m-%d"),
        y0=phosphorus_goal,
        y1=phosphorus_goal,
        line=dict(color="orange", width=2, dash="dash"),
    )
    nutrient_fig.add_annotation(
        x=nutrient_data['timestamp'].min(),
        y=phosphorus_goal,
        text="phosphorus Goal ("+str(phosphorus_goal)+" ppm)",
        showarrow=False,
        xanchor="right",
        font=dict(color="orange", size=12)
    )
    nutrient_fig.add_trace(go.Scatter(
        x=nutrient_data['timestamp'],
        y=nutrient_data['phosphorus'],
        mode='lines+markers',
        name='Phosphorus (P)',
        line=dict(color='orange')
    ))
    #potassium
    nutrient_fig.add_shape(
        type="line",
        x0=nutrient_data['timestamp'].min(),
        x1=(nutrient_data["timestamp"].max() + timedelta(days=8)).strftime("%Y-%m-%d"),
        y0=potassium_goal,
        y1=potassium_goal,
        line=dict(color="red", width=2, dash="dash"),
    )
    nutrient_fig.add_annotation(
        x=nutrient_data['timestamp'].min(),
        y=potassium_goal,
        text="Potassium Goal ("+str(potassium_goal)+" ppm)",
        showarrow=False,
        xanchor="right",
        font=dict(color="red", size=12)
    )
    nutrient_fig.add_trace(go.Scatter(
        x=nutrient_data['timestamp'],
        y=nutrient_data['potassium'],
        mode='lines+markers',
        name='Potassium (K)',
        line=dict(color='red')
    ))
    #prediction
    predicted_nitrogen_levels, predicted_phosphorus_levels, predicted_potassium_levels, predicted_fertilizing_days = predict_nutrients(nutrient_data, nitrogen_goal, phosphorus_goal, potassium_goal)
    start_timestamp = nutrient_data["timestamp"].max().strftime("%Y-%m-%d")
    future_timestamps = pd.date_range(start=start_timestamp, periods=9, freq='D')

    start_date = datetime(2025, 3, 12)
    for i in range(len(predicted_fertilizing_days) - 1):
        if predicted_fertilizing_days[i] == "1":
            nutrient_fig.add_shape(
                type="line",
                x0=start_date + timedelta(days=i),
                x1=start_date + timedelta(days=i),
                y0=0,
                y1=175,
                line=dict(color="green", width=2, dash="dash")
            )
    nutrient_fig.add_trace(go.Scatter(
        x=future_timestamps,
        y=predicted_nitrogen_levels,
        mode='lines+markers',
        name='Future Predicted Moisture',
        line=dict(color='cyan')
    ))
    nutrient_fig.add_trace(go.Scatter(
        x=future_timestamps,
        y=predicted_phosphorus_levels,
        mode='lines+markers',
        name='Future Predicted Moisture',
        line=dict(color='coral')
    ))
    nutrient_fig.add_trace(go.Scatter(
        x=future_timestamps,
        y=predicted_potassium_levels,
        mode='lines+markers',
        name='Future Predicted Moisture',
        line=dict(color='pink')
    ))
    nutrient_fig.add_shape(
        type="line",
        x0=nutrient_data["timestamp"].max(),
        x1=nutrient_data["timestamp"].max(),
        y0=0,
        y1=175,
        line=dict(color="gray", width=2, dash="dash")
    )
    nutrient_fig.add_annotation(
        x=nutrient_data["timestamp"].max(),
        y=175,
        text="Prediction line",
        font=dict(color="gray", size=12)
    )
    #final
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
