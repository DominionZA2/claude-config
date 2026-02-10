#!/usr/bin/env python3
"""
Back up all non-system MySQL databases from the test server using mysqldump.

Environment variables (sourced from ~/.claude/mysql.env):
  MYSQL_TEST_HOST, MYSQL_TEST_PORT, MYSQL_TEST_USER, MYSQL_TEST_PASSWORD
  MYSQL_BACKUP_DIR   – where to write the backup (default: ~/Backups/mysql)
  MYSQL_DUMP_PATH    – path to mysqldump binary
"""

import sys
import subprocess
import os
import datetime
import threading
import time


def check_and_install_packages():
    """Check for required packages and install if missing."""
    required_packages = {
        'mysql.connector': 'mysql-connector-python',
    }
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"Package {package_name} not found. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                print(f"Successfully installed {package_name}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {package_name}. Error: {e}")
                sys.exit(1)


check_and_install_packages()

import mysql.connector

# Connection details from environment variables
config = {
    'host': os.getenv('MYSQL_TEST_HOST'),
    'port': int(os.getenv('MYSQL_TEST_PORT', 3306)),
    'user': os.getenv('MYSQL_TEST_USER'),
    'password': os.getenv('MYSQL_TEST_PASSWORD')
}

# Backup directory
backup_dir = os.getenv('MYSQL_BACKUP_DIR', os.path.expanduser('~/Backups/mysql'))
os.makedirs(backup_dir, exist_ok=True)

# Generate backup filename
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = os.path.join(backup_dir, f'full_backup_{timestamp}.sql')

# Path to mysqldump
MYSQL_DUMP_PATH = os.getenv('MYSQL_DUMP_PATH', 'mysqldump')


def get_total_table_count():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys') "
        "AND TABLE_TYPE = 'BASE TABLE'"
    )
    total_tables = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return total_tables


def show_progress(total_tables):
    start_time = time.time()
    while not backup_complete.is_set():
        if os.path.exists(backup_file):
            with open(backup_file, 'rb') as f:
                current_tables = f.read().count(b'CREATE TABLE')
            progress = min(float(current_tables) / float(total_tables) * 100, 100)
            elapsed_time = int(time.time() - start_time)
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            print(f"\rProgress: {progress:.2f}% ({current_tables}/{total_tables} tables) | Time elapsed: {time_str}", end="", flush=True)
        time.sleep(1)


def execute_custom_sql_commands():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    try:
        custom_commands = [
            "DELETE FROM aura_cloud_device.PingHistory WHERE Time < DATE_SUB(NOW(), INTERVAL 7 DAY)",
        ]
        for command in custom_commands:
            print(f"Executing: {command}")
            cursor.execute(command)
            conn.commit()
        print("Custom SQL commands executed successfully")
    except mysql.connector.Error as err:
        print(f"Error executing custom SQL commands: {err}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Validate environment
    missing = [v for v in ('MYSQL_TEST_HOST', 'MYSQL_TEST_USER', 'MYSQL_TEST_PASSWORD') if not os.getenv(v)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        print("Source ~/.claude/mysql.env before running this script.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(MYSQL_DUMP_PATH) and MYSQL_DUMP_PATH != 'mysqldump':
        print(f"Error: mysqldump not found at {MYSQL_DUMP_PATH}")
        print("Set MYSQL_DUMP_PATH in ~/.claude/mysql.env")
        sys.exit(1)

    # Execute custom SQL commands
    execute_custom_sql_commands()

    # Get total table count
    total_tables = get_total_table_count()
    print(f"Total tables to backup: {total_tables}")

    # Flag to signal backup completion
    backup_complete = threading.Event()

    # Start progress thread
    progress_thread = threading.Thread(target=show_progress, args=(total_tables,))
    progress_thread.start()

    # Execute mysqldump for each database separately
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    databases = [db[0] for db in cursor.fetchall()
                 if db[0] not in ['information_schema', 'mysql', 'performance_schema', 'sys']]

    try:
        with open(backup_file, 'wb') as f:
            for db in databases:
                mysqldump_cmd = [
                    MYSQL_DUMP_PATH,
                    f'--host={config["host"]}',
                    f'--port={config["port"]}',
                    f'--user={config["user"]}',
                    f'--password={config["password"]}',
                    '--single-transaction',
                    '--quick',
                    '--lock-tables=false',
                    '--set-gtid-purged=OFF',
                    '--compress',
                    '--skip-triggers',
                    '--databases',
                    db
                ]
                subprocess.run(mysqldump_cmd, stdout=f, stderr=subprocess.PIPE, check=True)

        backup_complete.set()
        progress_thread.join()
        print(f"\nBackup completed successfully. File saved as: {backup_file}")
    except subprocess.CalledProcessError as e:
        backup_complete.set()
        progress_thread.join()
        print(f"\nBackup failed. Error: {e.stderr.decode()}")
    finally:
        cursor.close()
        conn.close()
