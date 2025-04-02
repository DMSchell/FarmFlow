import pandas as pd

def predict_moisture(moisture_data, moisture_goal):
    prediction_period = 9
    df = moisture_data
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 86400
    df['moisture_diff'] = df['moisture_level'].diff()

    watered_data = df[df['watering'] == '1']
    non_watered_data = df[df['watering'] == '0']

    avg_increase_rate = watered_data['moisture_diff'].sum() / watered_data['time_diff'].sum()
    avg_decrease_rate = non_watered_data['moisture_diff'].sum() / non_watered_data['time_diff'].sum()

    current_moisture = df['moisture_level'].iloc[-1]
    predicted_moisture_levels = []
    predicted_watering_days = []
    predicted_moisture_levels.append(current_moisture)

    for day in range(prediction_period):
        if current_moisture < moisture_goal:
            current_moisture += avg_increase_rate
            predicted_watering_days.append("1") 
        else:
            current_moisture += avg_decrease_rate
            predicted_watering_days.append("0")
        predicted_moisture_levels.append(current_moisture)

    return predicted_moisture_levels, predicted_watering_days