import sqlite3
import pandas as pd

def init_nutrient_db():
    conn = sqlite3.connect("soil_nutrients.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS nutrient_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sensor_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        nitrogen REAL,
                        phosphorus REAL,
                        potassium REAL
                    )''')
    conn.commit()
    conn.close()

def nutrient_insert_data(sensor_id, timestamp, nitrogen, phosphorus, potassium):
    conn = sqlite3.connect("soil_nutrients.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO nutrient_data (sensor_id, timestamp, nitrogen, phosphorus, potassium) VALUES (?, ?, ?, ?, ?)", 
        (sensor_id, timestamp, nitrogen, phosphorus, potassium))
    conn.commit()
    conn.close()

def nutrient_import_from_csv(file_path):
    conn = sqlite3.connect("soil_nutrients.db")
    df = pd.read_csv(file_path)
    df.to_sql("nutrient_data", conn, if_exists="append", index=False)
    conn.close()

if __name__ == "__main__":
    init_nutrient_db()
