import sqlite3
import pandas as pd

def init_moisture_db():
    conn = sqlite3.connect("soil_moisture.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS moisture_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sensor_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        moisture_level REAL,
                        watering TEXT
                    )''')
    conn.commit()
    conn.close()

def moisture_insert_data(sensor_id, moisture_level, timestamp, watering):
    conn = sqlite3.connect("soil_moisture.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO moisture_data (sensor_id, moisture_level, timestamp, watering) VALUES (?, ?, ?, ?)", 
        (sensor_id, moisture_level, timestamp, watering))
    conn.commit()
    conn.close()

def moisture_import_from_csv(file_path):
    conn = sqlite3.connect("soil_moisture.db")
    df = pd.read_csv(file_path)
    df.to_sql("moisture_data", conn, if_exists="append", index=False)
    conn.close()

if __name__ == "__main__":
    init_moisture_db()
