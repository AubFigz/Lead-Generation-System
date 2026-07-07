import requests
from sqlalchemy import create_engine

def check_database(db_config):
    try:
        engine = create_engine(
            f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
        )
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("Database connection successful.")
    except Exception as e:
        print(f"Database connection failed: {e}")

def check_api(api_url):
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            print("API is healthy.")
        else:
            print(f"API health check failed with status code: {response.status_code}")
    except Exception as e:
        print(f"API health check failed: {e}")

if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "user": "your_user",
        "password": "your_password",
        "database": "lead_data"
    }
    api_url = "https://jsonplaceholder.typicode.com/posts"

    check_database(db_config)
    check_api(api_url)
