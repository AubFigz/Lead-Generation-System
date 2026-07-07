import asyncio
import aiohttp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import pool
import logging
import diskcache as dc
from dask import delayed, compute
from dask.distributed import Client
from tenacity import retry, stop_after_attempt, wait_exponential
from pytz import timezone
from datetime import datetime
import yaml
from logging.handlers import RotatingFileHandler
import boto3
from google.cloud import storage
import pandas as pd

# Setup logging
def setup_logging(config):
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

# Initialize cache
def init_cache(cache_path):
    logging.info(f"Initializing cache at {cache_path}.")
    return dc.Cache(cache_path)

# Initialize PostgreSQL connection pool
DB_POOL = None

def init_db_pool(db_config):
    global DB_POOL
    try:
        DB_POOL = psycopg2.pool.SimpleConnectionPool(
            1, db_config['connection_pool']['max'],
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            connect_timeout=db_config['timeout']
        )
        logging.info("Database connection pool created successfully.")
    except Exception as e:
        logging.error(f"Error creating database connection pool: {e}")
        raise

# Initialize Selenium WebDriver
def init_driver(driver_path):
    try:
        service = Service(driver_path)
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Selenium WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"Error initializing Selenium WebDriver: {e}")
        return None

# Localize timestamps
def localize_timestamp(timestamp, tz_string):
    try:
        tz = timezone(tz_string)
        localized_timestamp = timestamp.astimezone(tz)
        logging.info(f"Timestamp localized to {tz_string}.")
        return localized_timestamp
    except Exception as e:
        logging.error(f"Error localizing timestamp: {e}")
        raise

# Scrape properties from LoopNet
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
def scrape_loopnet_properties(url, driver_path, timeout):
    if url in cache:
        logging.info(f"Loading cached data for {url}.")
        return cache[url]

    driver = init_driver(driver_path)
    if not driver:
        logging.error("Failed to initialize driver. Exiting LoopNet scraping.")
        return []

    try:
        logging.info(f"Navigating to {url}.")
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'property-card'))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        listings = soup.find_all('div', class_='property-card')

        properties = []
        for listing in listings:
            name = listing.find('h2').text.strip() if listing.find('h2') else 'N/A'
            address = listing.find('address').text.strip() if listing.find('address') else 'N/A'
            price = listing.find('span', class_='price').text.strip() if listing.find('span', 'price') else 'N/A'
            property_type = listing.find('span', class_='property-type').text.strip() if listing.find('span', 'property-type') else 'N/A'
            area = listing.find('span', class_='property-size').text.strip() if listing.find('span', 'property-size') else 'N/A'
            status = listing.find('span', class_='property-status').text.strip() if listing.find('span', 'property-status') else 'N/A'
            properties.append((name, address, price, property_type, area, status))

        logging.info(f"Scraped {len(properties)} properties from {url}.")
        cache[url] = properties
        return properties
    except Exception as e:
        logging.error(f"Error scraping properties from {url}: {e}")
        return []
    finally:
        driver.quit()

# Store properties in PostgreSQL
async def store_properties_in_db(properties, table_name, batch_insert_size):
    if not properties:
        logging.info("No properties to store in the database.")
        return

    try:
        conn = DB_POOL.getconn()
        cur = conn.cursor()

        cur.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                address VARCHAR(255),
                price VARCHAR(50),
                property_type VARCHAR(100),
                area VARCHAR(100),
                status VARCHAR(50),
                scraped_at TIMESTAMP
            )
        ''')

        now = localize_timestamp(datetime.now(), config['system']['timezone'])
        properties_with_timestamp = [(p[0], p[1], p[2], p[3], p[4], p[5], now) for p in properties]

        for i in range(0, len(properties_with_timestamp), batch_insert_size):
            batch = properties_with_timestamp[i:i + batch_insert_size]
            insert_query = f"INSERT INTO {table_name} (name, address, price, property_type, area, status, scraped_at) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cur.executemany(insert_query, batch)

        conn.commit()
        logging.info(f"Successfully stored {len(properties)} properties in the database table {table_name}.")
        cur.close()
    except Exception as e:
        logging.error(f"Error storing properties in the database: {e}")
    finally:
        if conn:
            DB_POOL.putconn(conn)

# Save to Cloud Storage
def save_to_cloud(properties, cloud_storage, table_name):
    if not properties or not cloud_storage.get('enabled', False):
        return

    file_name = f"{table_name}.csv"
    try:
        pd.DataFrame(properties, columns=["name", "address", "price", "property_type", "area", "status", "scraped_at"]).to_csv(file_name, index=False)

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

# Main flow
if __name__ == "__main__":
    config = load_config()
    setup_logging(config)

    init_db_pool(config['database'])

    loopnet_url = config['real_estate']['url']
    driver_path = config['real_estate']['driver_path']
    table_name = config['real_estate']['table_name']
    num_pages_to_scrape = config['real_estate']['num_pages']
    cache_path = config['real_estate']['cache_path']
    timeout = config['real_estate']['timeout']
    batch_insert_size = config['real_estate']['batch_insert_size']

    cache = init_cache(cache_path)

    # Distributed scraping
    client = Client()
    tasks = [
        delayed(scrape_loopnet_properties)(f"{loopnet_url}?page={page_num}", driver_path, timeout)
        for page_num in range(1, num_pages_to_scrape + 1)
    ]
    results = compute(*tasks)
    loopnet_properties = [item for sublist in results for item in sublist]

    # Store scraped data
    asyncio.run(store_properties_in_db(loopnet_properties, table_name, batch_insert_size))

    # Save to cloud storage
    save_to_cloud(loopnet_properties, config['advanced']['cloud_storage'], table_name)

    if DB_POOL:
        DB_POOL.closeall()
        logging.info("Database connection pool closed.")
