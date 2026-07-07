import schedule
import time
import subprocess
import logging
import yaml
from logging.handlers import RotatingFileHandler


def setup_logging(config):
    log_file = config['logging']['file']
    max_file_size = int(config['logging']['max_file_size'].replace('MB', '')) * 1024 * 1024
    handler = RotatingFileHandler(log_file, maxBytes=max_file_size,
                                  backupCount=config['logging']['backup_count'])
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[handler, logging.StreamHandler()])
    logging.info("Logging initialized successfully.")


def load_config(config_file="config.yaml"):
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        logging.info("Configuration file loaded successfully.")
        return config
    except Exception as e:
        logging.error(f"Error loading configuration file: {e}")
        raise


def execute_script(script_name, config=None):
    """Run a script as a subprocess. Raises on any failure so the caller (or a
    scheduler) can react, rather than silently swallowing a non-zero exit."""
    logging.info(f"Starting execution: {script_name}")
    try:
        result = subprocess.run(["python", script_name], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
    except Exception as e:
        logging.error(f"Exception while executing {script_name}: {e}")
        raise Exception(f"Exception while executing {script_name}: {e}")

    if result.returncode == 0:
        logging.info(f"Script {script_name} executed successfully.")
        return result

    logging.error(f"Exception while executing {script_name}: return code {result.returncode}")
    raise Exception(f"Exception while executing {script_name}: return code {result.returncode}")


def schedule_tasks(config):
    """Schedule tasks from config. Unknown intervals are logged as errors and skipped."""
    for task in config['task_scheduler']['tasks']:
        script = task.get('script')
        time_of_day = task.get('time')
        interval = task.get('interval', 'day')

        if not script:
            logging.warning("Skipping task with missing 'script' key.")
            continue

        if interval == "minute":
            schedule.every().minute.do(execute_script, script_name=script)
        elif interval == "hour":
            schedule.every().hour.do(execute_script, script_name=script)
        elif interval == "day" and time_of_day:
            schedule.every().day.at(time_of_day).do(execute_script, script_name=script)
        elif interval == "week":
            schedule.every().week.do(execute_script, script_name=script)
        else:
            logging.error(f"Unknown interval {interval} for script {script}.")
            continue

        logging.info(f"Scheduled {script} at {time_of_day or 'default time'} ({interval}).")


def main():
    config = load_config()
    setup_logging(config)
    schedule_tasks(config)
    logging.info("Task scheduler initialized and tasks scheduled.")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
