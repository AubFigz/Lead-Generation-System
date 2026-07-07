import logging
import time
from datetime import datetime
import yaml
from logging.handlers import RotatingFileHandler


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


# Monitor scraping processes
def monitor_scraping_process(scraper_name, status, retries, retry_limit, additional_info=None):
    """
    Monitors the scraping process and logs its status.

    Args:
        scraper_name (str): Name of the scraper being monitored.
        status (str): Status of the process ("SUCCESS", "FAILURE", "IN_PROGRESS").
        retries (int): Current retry attempt.
        retry_limit (int): Maximum retry attempts.
        additional_info (dict): Additional information to log (e.g., URLs, error messages).

    Returns:
        None
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"[{timestamp}] {scraper_name}: Status={status}, Retries={retries}/{retry_limit}"

    if additional_info:
        additional_details = ", ".join(f"{key}={value}" for key, value in additional_info.items())
        message += f", Details: {additional_details}"

    if status == "FAILURE":
        logging.error(message)
    elif status == "SUCCESS":
        logging.info(message)
    else:  # Default to INFO for "IN_PROGRESS" or other statuses
        logging.info(message)


# Example monitoring implementation
def scrape_example(config):
    """
    Example scraping process with monitoring and retry logic.
    """
    scraper_name = "ExampleScraper"
    retry_limit = config['system']['max_retries']
    retry_backoff = config['system']['retry_backoff']

    retries = 0
    success = False

    while retries < retry_limit and not success:
        try:
            monitor_scraping_process(scraper_name, "IN_PROGRESS", retries, retry_limit)

            # Simulate scraping process
            time.sleep(2)  # Simulate processing time
            if retries < 2:  # Simulate transient errors
                raise ValueError("Simulated scraping error.")

            # Mark as successful
            monitor_scraping_process(scraper_name, "SUCCESS", retries, retry_limit,
                                     {"message": "Scraping completed successfully."})
            success = True

        except Exception as e:
            retries += 1
            monitor_scraping_process(scraper_name, "FAILURE", retries, retry_limit, {"error": str(e)})
            if retries < retry_limit:
                logging.info(f"Retrying in {retry_backoff} seconds...")
                time.sleep(retry_backoff)
            else:
                logging.error(f"Exceeded maximum retries ({retry_limit}). Scraper failed.")


if __name__ == "__main__":
    # Load configuration and setup logging
    config = load_config("config.yaml")
    setup_logging(config)

    # Example scraping monitoring
    scrape_example(config)
