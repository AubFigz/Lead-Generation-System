import psycopg2
import os
import logging
import yaml
import gzip
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import text
from config_loader import load_config


def setup_logging(config):
    try:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.FileHandler(config['logging']['file']), logging.StreamHandler()],
        )
    except Exception as e:
        logging.error(f"Error setting up logging: {e}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def cleanup_table(table_name, retention_days, db_config=None, connection=None):
    """Delete rows older than `retention_days`.

    The cutoff is computed in Python so the DELETE is portable across databases
    (no Postgres-only `interval` syntax). Pass a SQLAlchemy `connection` to run
    against any engine (used in tests against in-memory SQLite); otherwise a
    psycopg2 connection is opened from `db_config`.
    """
    cutoff = datetime.now() - timedelta(days=retention_days)

    if connection is not None:
        result = connection.execute(
            text(f"DELETE FROM {table_name} WHERE created_at < :cutoff"), {"cutoff": cutoff}
        )
        deleted = result.rowcount
        logging.info(f"Deleted {deleted} rows from table {table_name}.")
        return deleted

    conn = None
    try:
        conn = psycopg2.connect(
            host=db_config['host'], database=db_config['database'],
            user=db_config['user'], password=db_config['password'],
        )
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {table_name} WHERE created_at < %s", (cutoff,))
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        logging.info(f"Deleted {deleted} rows from table {table_name}.")
        return deleted
    except Exception as e:
        logging.error(f"Error cleaning up table {table_name}: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def backup_database(config):
    db_config = config['database']
    backup_dir = config['advanced']['backup_directory']
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_file = os.path.join(backup_dir, f"lead_data_backup_{timestamp}.sql.gz")
    try:
        with gzip.open(backup_file, 'wb') as gzipped_file:
            os.system(
                f"pg_dump -U {db_config['user']} -h {db_config['host']} "
                f"-p {db_config['port']} -F c {db_config['database']} > backup.sql"
            )
            with open("backup.sql", 'rb') as plain_backup:
                gzipped_file.writelines(plain_backup)
            os.remove("backup.sql")
        logging.info(f"Database backup created and compressed at {backup_file}.")
        return backup_file
    except Exception as e:
        logging.error(f"Error creating database backup: {e}")
        raise


def upload_backup_to_cloud(backup_file, cloud_config):
    if not cloud_config.get('enabled', False):
        logging.info("Cloud storage is disabled in the configuration.")
        return
    provider = cloud_config.get('provider')
    if provider == 'aws':
        import boto3
        s3 = boto3.client('s3', region_name=cloud_config['region'])
        s3.upload_file(backup_file, cloud_config['bucket_name'], os.path.basename(backup_file))
        logging.info(f"Backup uploaded to AWS S3 bucket {cloud_config['bucket_name']}.")
    elif provider == 'gcp':
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(cloud_config['bucket_name'])
        bucket.blob(os.path.basename(backup_file)).upload_from_filename(backup_file)
        logging.info(f"Backup uploaded to GCP bucket {cloud_config['bucket_name']}.")
    else:
        raise ValueError(f"Unsupported cloud provider: {provider}")


if __name__ == "__main__":
    config = load_config()
    setup_logging(config)
    retention_days = config['system'].get('data_retention_days', 90)
    db_config = config['database']
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(cleanup_table, t, retention_days, db_config)
                   for t in config['preprocessing']['tables'].values()]
        for future in futures:
            future.result()
    try:
        backup_file_path = backup_database(config)
        if backup_file_path:
            upload_backup_to_cloud(backup_file_path, config['advanced']['cloud_storage'])
    except Exception as e:
        logging.error(f"Error during database backup: {e}")
