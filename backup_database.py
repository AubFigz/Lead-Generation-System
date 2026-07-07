import os
import subprocess
from datetime import datetime

def backup_database(db_config):
    """
    Backup the database using `pg_dump` and save it to a timestamped file.
    Args:
        db_config (dict): Database configuration containing host, user, and database name.
    """
    backup_dir = './backups'
    os.makedirs(backup_dir, exist_ok=True)
    filename = f"{backup_dir}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    cmd = (
        f"PGPASSWORD={db_config['password']} "
        f"pg_dump -h {db_config['host']} -U {db_config['user']} {db_config['database']} > {filename}"
    )
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"Backup saved to {filename}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to backup database: {e}")

# Example usage
if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "user": "your_user",
        "password": "your_password",
        "database": "lead_data"
    }
    backup_database(db_config)
