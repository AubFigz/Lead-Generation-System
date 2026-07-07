import logging
import psycopg2
from psycopg2 import pool, DatabaseError
from logging.handlers import RotatingFileHandler
import yaml
import time
from datetime import datetime

# Setup logging with dynamic configuration
def setup_logging(config):
    try:
        handler = RotatingFileHandler(
            config['logging']['file'],
            maxBytes=int(config['logging']['max_file_size'].replace('MB', '')) * 1024 * 1024,
            backupCount=config['logging']['backup_count']
        )
        logging.basicConfig(
            level=getattr(logging, config['logging']['level'].upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[handler, logging.StreamHandler()]
        )
        logging.info("Logging setup completed.")
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

# Initialize database connection pool
def init_db_pool(config):
    try:
        db_config = config['database']
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            db_config['connection_pool']['min'],
            db_config['connection_pool']['max'],
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            connect_timeout=db_config['timeout']
        )
        logging.info("Database connection pool initialized successfully.")
        return connection_pool
    except DatabaseError as e:
        logging.error(f"Error initializing database connection pool: {e}")
        raise

# Monitor database connections
def monitor_db_connections(connection_pool, retry_limit, retry_backoff):
    """
    Monitors the database connection pool and logs metrics.

    Args:
        connection_pool (SimpleConnectionPool): Database connection pool to monitor.
        retry_limit (int): Number of retry attempts in case of failure.
        retry_backoff (int): Time (in seconds) to wait between retries.

    Returns:
        bool: True if all connections are successful, False otherwise.
    """
    retries = 0
    while retries < retry_limit:
        try:
            conn = connection_pool.getconn()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")  # Simple query to check connection health
                    logging.info("Database connection check successful.")
                connection_pool.putconn(conn)
                return True
        except DatabaseError as e:
            retries += 1
            logging.warning(f"Database connection check failed: {e}. Retry {retries}/{retry_limit}.")
            if retries < retry_limit:
                time.sleep(retry_backoff)
            else:
                logging.error("Exceeded maximum retry attempts for database connection.")
                return False
        finally:
            if 'conn' in locals() and conn:
                connection_pool.putconn(conn, close=True)

# Log pool metrics
def log_pool_metrics(connection_pool):
    """
    Logs the current status of the database connection pool.

    Args:
        connection_pool (SimpleConnectionPool): Database connection pool to monitor.
    """
    try:
        available = connection_pool._used
        max_connections = connection_pool._maxconn
        min_connections = connection_pool._minconn
        logging.info(f"Database Connection Pool Metrics - Available: {available}, Min: {min_connections}, Max: {max_connections}")
    except Exception as e:
        logging.error(f"Error retrieving connection pool metrics: {e}")

# Main flow
if __name__ == "__main__":
    # Load configuration
    config = load_config("config.yaml")
    setup_logging(config)

    retry_limit = config['system']['max_retries']
    retry_backoff = config['system']['retry_backoff']

    # Initialize database connection pool
    connection_pool = init_db_pool(config)

    # Monitor database connections
    success = monitor_db_connections(connection_pool, retry_limit, retry_backoff)
    if success:
        logging.info("All database connections are healthy.")
    else:
        logging.error("Database connections are not healthy.")

    # Log database connection pool metrics
    log_pool_metrics(connection_pool)

    # Close the connection pool
    if connection_pool:
        connection_pool.closeall()
        logging.info("Database connection pool closed.")
