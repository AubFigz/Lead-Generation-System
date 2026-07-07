import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import logging
import yaml
import os
from datetime import datetime
from time import sleep
from pytz import timezone as pytz_timezone
from config_loader import load_config


def setup_logging(config):
    try:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.FileHandler(config['logging']['file']), logging.StreamHandler()],
        )
    except Exception as e:
        print(f"Error setting up logging: {e}")
        raise


def notify_stakeholders(email_recipients, subject, message, config):
    """Send an email with retries. Uses safe config access, and raises if every
    attempt fails so the caller knows delivery did not succeed."""
    smtp_config = config.get('notifications')
    if not smtp_config or not smtp_config.get('enabled', False):
        logging.warning("Email notifications are disabled in the configuration.")
        return

    smtp_server = smtp_config.get('smtp_server')
    sender_email = smtp_config.get('sender_email')
    password = smtp_config.get('email_auth', {}).get('password')
    port = smtp_config.get('port', 465)

    if not all([smtp_server, sender_email, password]):
        logging.error("SMTP configuration is incomplete.")
        return

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ", ".join(email_recipients)
    msg.attach(MIMEText(message, 'plain'))

    system_config = config.get('system', {})
    retry_attempts = system_config.get('max_retries', 3)
    retry_backoff = system_config.get('retry_backoff', 2)

    for attempt in range(retry_attempts):
        try:
            server = smtplib.SMTP_SSL(smtp_server, port)
            server.login(sender_email, password)
            server.sendmail(sender_email, email_recipients, msg.as_string())
            server.quit()
            logging.info(f"Email notification sent to: {', '.join(email_recipients)}")
            return
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} to send email failed: {e}")
            if attempt < retry_attempts - 1:
                sleep(retry_backoff)
            else:
                logging.error(f"Failed to send email after {retry_attempts} attempts.")
                raise


def export_to_csv(dataframe, file_name, config):
    """Write a dataframe to CSV under the configured export directory. Errors
    (e.g. a non-existent directory) propagate rather than being swallowed."""
    export_dir = config.get('export', {}).get('directory', './exports')
    os.makedirs(export_dir, exist_ok=True)
    full_path = os.path.join(str(export_dir), file_name)

    if dataframe.empty:
        logging.warning("Export aborted: DataFrame is empty.")
        return

    dataframe.to_csv(full_path, index=False)
    logging.info(f"Leads exported to {full_path}. Total leads: {len(dataframe)}")


def get_localized_timestamp(config):
    try:
        tz = pytz_timezone(config['system']['timezone'])
        return datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logging.error(f"Error localizing timestamp: {e}")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
