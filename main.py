from backend.moisture_database import init_moisture_db
from backend.nutrients_database import init_nutrient_db
from frontend.app import app

def run_application():
    # Initialize the database (only needs to run once)
    init_moisture_db()
    init_nutrient_db()
    
    # Run the web application (Flask)
    app.run(debug=True)

if __name__ == "__main__":
    run_application()
