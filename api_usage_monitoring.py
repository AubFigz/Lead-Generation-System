import logging
import requests
import yaml
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from tenacity import retry, stop_after_attempt, wait_exponential

# Setup logging
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

# Monitor API usage
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
def monitor_api_usage(api_url, headers, params=None):
    """
    Monitor the API usage by making a request and logging the response.
    Args:
        api_url (str): API endpoint to monitor.
        headers (dict): HTTP headers for the request.
        params (dict): Query parameters for the request.
    Returns:
        dict: API response JSON.
    """
    try:
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code == 429:  # Too Many Requests
            retry_after = int(response.headers.get("Retry-After", 5))
            logging.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            raise Exception("Rate limit exceeded.")
        response.raise_for_status()
        logging.info(f"API call to {api_url} successful. Status code: {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during API call to {api_url}: {e}")
        raise

# Log API usage metrics
def log_api_metrics(api_response, config):
    """
    Logs API usage metrics like response time, rate limits, etc.
    Args:
        api_response (dict): API response JSON.
        config (dict): Configuration dictionary.
    """
    try:
        rate_limit = api_response.get("rate_limit", {})
        usage_limit = rate_limit.get("limit", "Unknown")
        usage_remaining = rate_limit.get("remaining", "Unknown")
        usage_reset = rate_limit.get("reset", "Unknown")
        logging.info(f"API Usage Metrics - Limit: {usage_limit}, Remaining: {usage_remaining}, Reset: {usage_reset}")
    except KeyError as e:
        logging.error(f"Missing key in API response metrics: {e}")
    except Exception as e:
        logging.error(f"Error logging API metrics: {e}")

# Save metrics to file
def save_metrics_to_file(metrics, file_path):
    """
    Save API usage metrics to a file for long-term tracking.
    Args:
        metrics (dict): API usage metrics.
        file_path (str): Path to the file where metrics will be saved.
    """
    try:
        with open(file_path, "a") as file:
            file.write(f"{datetime.now()}: {metrics}\n")
        logging.info(f"Metrics saved to {file_path}.")
    except Exception as e:
        logging.error(f"Error saving metrics to file: {e}")

if __name__ == "__main__":
    # Load configuration
    config = load_config("config.yaml")
    setup_logging(config)

    api_url = config['api_monitoring']['api_url']
    headers = config['api_monitoring']['headers']
    params = config['api_monitoring'].get('params', {})
    metrics_file = config['api_monitoring'].get('metrics_file', "api_metrics.log")

    # Monitor API usage
    try:
        api_response = monitor_api_usage(api_url, headers, params)
        log_api_metrics(api_response, config)
        save_metrics_to_file(api_response, metrics_file)
    except Exception as e:
        logging.error(f"API monitoring failed: {e}")
