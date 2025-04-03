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

def predict_nutrients(nutrient_data, nitrogen_goal, phosphorus_goal, potassium_goal):
    prediction_period = 9
    df = nutrient_data
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 86400
    df['nitrogen_diff'] = df['nitrogen'].diff()
    df['phosphorus_diff'] = df['phosphorus'].diff()
    df['potassium_diff'] = df['potassium'].diff()

    fertilized_data = df[df['fertilized'] == '1']
    non_fertilized_data = df[df['fertilized'] == '0']

    nitrogen_avg_increase_rate = fertilized_data['nitrogen_diff'].sum() / fertilized_data['time_diff'].sum()  
    nitrogen_avg_decrease_rate = non_fertilized_data['nitrogen_diff'].sum() / non_fertilized_data['time_diff'].sum()
    phosphorus_avg_increase_rate = fertilized_data['phosphorus_diff'].sum() / fertilized_data['time_diff'].sum()  
    phosphorus_avg_decrease_rate = non_fertilized_data['phosphorus_diff'].sum() / non_fertilized_data['time_diff'].sum() 
    potassium_avg_increase_rate = fertilized_data['potassium_diff'].sum() / fertilized_data['time_diff'].sum()  
    potassium_avg_decrease_rate = non_fertilized_data['potassium_diff'].sum() / non_fertilized_data['time_diff'].sum()

    predicted_fertilizing_days = []
    current_nitrogen = df['nitrogen'].iloc[-1]
    predicted_nitrogen_levels = []
    predicted_nitrogen_levels.append(current_nitrogen)
    current_phosphorus = df['phosphorus'].iloc[-1]
    predicted_phosphorus_levels = []
    predicted_phosphorus_levels.append(current_phosphorus)
    current_potassium = df['potassium'].iloc[-1]
    predicted_potassium_levels = []
    predicted_potassium_levels.append(current_potassium)

    for day in range(prediction_period):
        nitrogen_condition = current_nitrogen < nitrogen_goal
        phosphorus_condition = current_phosphorus < phosphorus_goal
        potassium_condition = current_potassium < potassium_goal
        if sum([nitrogen_condition, phosphorus_condition, potassium_condition]) >= 2:
            current_nitrogen += nitrogen_avg_increase_rate
            current_phosphorus += phosphorus_avg_increase_rate
            current_potassium += potassium_avg_increase_rate
            predicted_fertilizing_days.append("1") 
        else:
            current_nitrogen += nitrogen_avg_decrease_rate
            current_phosphorus += phosphorus_avg_decrease_rate
            current_potassium += potassium_avg_decrease_rate
            predicted_fertilizing_days.append("0")
        predicted_nitrogen_levels.append(current_nitrogen)
        predicted_phosphorus_levels.append(current_phosphorus)
        predicted_potassium_levels.append(current_potassium)

    return predicted_nitrogen_levels, predicted_phosphorus_levels, predicted_potassium_levels, predicted_fertilizing_days