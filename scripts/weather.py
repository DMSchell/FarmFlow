import requests
import pandas as pd

def fetch_weather_data(latitude, longitude, start_date, end_date):
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,precipitation,relative_humidity_2m&start_date={start_date}&end_date={end_date}&timezone=UTC"
    response = requests.get(url)
    data = response.json()

    if "hourly" not in data:
        return None
    
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(data["hourly"]["time"]),
        "temperature_c": data["hourly"]["temperature_2m"],
        "precipitation": data["hourly"]["precipitation"],
        "humidity": data["hourly"]["relative_humidity_2m"]
    })
    df["temperature_f"] = df["temperature_c"] * 1.8 + 32

    return df
