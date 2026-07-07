import requests
from bs4 import BeautifulSoup
import psycopg2
import logging
import yaml
from time import sleep
from tenacity import retry, stop_after_attempt, wait_exponential
from pytz import timezone
from datetime import datetime
import boto3
from google.cloud import storage
from logging.handlers import RotatingFileHandler
import pandas as pd

# Setup logging
def setup_logging(config):
    try:
        handler = RotatingFileHandler(
            config['logging']['file'],
            maxBytes=int(config['logging']['max_file_size'].replace('MB', '')) * 1024 * 1024,
            backupCount=config['logging']['backup_count']
        )
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[handler, logging.StreamHandler()]
        )
        logging.info("Logging setup complete.")
    except Exception as e:
        print(f"Error setting up logging: {e}")
        raise

# Load configuration
def load_config(config_file="config.yaml"):
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        logging.info("Configuration file loaded successfully.")
        return config
    except Exception as e:
        logging.error(f"Error loading configuration file: {e}")
        raise

# Apply timezone and locale to timestamps
def localize_timestamp(timestamp, tz_string):
    try:
        tz = timezone(tz_string)
        localized_timestamp = timestamp.astimezone(tz)
        logging.info(f"Timestamp localized to {tz_string}.")
        return localized_timestamp
    except Exception as e:
        logging.error(f"Error localizing timestamp: {e}")
        raise

# Scrape Construction Projects with Retry Logic
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
def scrape_construction_projects(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        projects = []
        for project in soup.find_all('div', class_='project-card'):  # Adjust class based on site
            name = project.find('h2').text.strip() if project.find('h2') else None
            contractor = project.find('div', class_='contractor-name').text.strip() if project.find('div', 'contractor-name') else None
            location = project.find('div', class_='project-location').text.strip() if project.find('div', 'project-location') else None
            projects.append((name, contractor, location))

        logging.info(f"Scraped {len(projects)} projects from {url}.")
        return projects
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error while scraping {url}: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while scraping {url}: {e}")
        raise

# Store Construction Leads in PostgreSQL
def store_projects_in_db(projects, db_config, table_name):
    if not projects:
        logging.info("No projects to store in the database.")
        return

    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        cur = conn.cursor()

        create_table_query = f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                project_name VARCHAR(255),
                contractor VARCHAR(255),
                location VARCHAR(255),
                scraped_at TIMESTAMP
            )
        '''
        cur.execute(create_table_query)

        now = datetime.now()
        projects_with_timestamp = [(p[0], p[1], p[2], now) for p in projects]

        insert_query = f'''
            INSERT INTO {table_name} (project_name, contractor, location, scraped_at)
            VALUES (%s, %s, %s, %s)
        '''
        cur.executemany(insert_query, projects_with_timestamp)
        conn.commit()

        logging.info(f"Successfully stored {len(projects)} projects in the database table {table_name}.")
        cur.close()
    except Exception as e:
        logging.error(f"Error storing projects in the database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# Save to Cloud Storage
def save_to_cloud(projects, cloud_storage, table_name):
    if not projects or not cloud_storage.get('enabled', False):
        return

    file_name = f"{table_name}.csv"
    try:
        pd.DataFrame(projects, columns=["project_name", "contractor", "location", "scraped_at"]).to_csv(file_name, index=False)

        if cloud_storage['provider'] == 'aws':
            s3 = boto3.client('s3', region_name=cloud_storage.get('region', 'us-east-1'))
            s3.upload_file(file_name, cloud_storage['bucket_name'], file_name)
            logging.info(f"Data successfully uploaded to AWS S3 bucket {cloud_storage['bucket_name']} as {file_name}.")
        elif cloud_storage['provider'] == 'gcp':
            client = storage.Client(project=cloud_storage.get('gcp_project'))
            bucket = client.bucket(cloud_storage['bucket_name'])
            blob = bucket.blob(file_name)
            blob.upload_from_filename(file_name)
            logging.info(f"Data successfully uploaded to GCP bucket {cloud_storage['bucket_name']} as {file_name}.")
    except Exception as e:
        logging.error(f"Error uploading to cloud storage: {e}")

if __name__ == "__main__":
    config = load_config()
    setup_logging(config)

    url = config['construction']['url']
    table_name = config['construction']['table_name']
    retry_attempts = config['construction'].get('retry_attempts', 3)
    user_agent = config['construction']['user_agent']
    headers = {'User-Agent': user_agent}

    projects = []
    for attempt in range(retry_attempts):
        try:
            projects = scrape_construction_projects(url, headers)
            break
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            sleep(config['system'].get('retry_backoff', 2))

    projects = [(p[0], p[1], p[2], localize_timestamp(datetime.now(), config['system']['timezone'])) for p in projects]

    store_projects_in_db(projects, config['database'], table_name)
    save_to_cloud(projects, config['advanced']['cloud_storage'], table_name)
