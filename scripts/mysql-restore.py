#!/usr/bin/env python3
"""
Restore a MySQL backup file to the local MySQL server.

Usage:
    python3 mysql-restore.py <backup_file>

Environment variables (sourced from ~/.claude/mysql.env):
  MYSQL_LOCAL_HOST, MYSQL_LOCAL_PORT, MYSQL_LOCAL_USER, MYSQL_LOCAL_PASSWORD
"""

import sys
import subprocess


def check_and_install_packages():
    """Check for required packages and install if missing."""
    required_packages = {
        'mysqlclient': 'mysqlclient',
    }
    for import_name, package_name in required_packages.items():
        try:
            if import_name == 'mysqlclient':
                __import__('MySQLdb')
            else:
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

import os
import time
import re
import MySQLdb

config = {
    'host': os.getenv('MYSQL_LOCAL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_LOCAL_PORT', 3306)),
    'user': os.getenv('MYSQL_LOCAL_USER'),
    'password': os.getenv('MYSQL_LOCAL_PASSWORD'),
    'charset': 'utf8mb4',
    'use_unicode': True,
}


def print_config_and_prompt(restore_file):
    print("Current configuration:")
    print(f"Host: {config['host']}")
    print(f"Port: {config['port']}")
    print(f"User: {config['user']}")
    print(f"Password: {'*' * len(config['password'] or '')}")
    print(f"Restore file: {restore_file}")

    while True:
        response = input("\nDo you want to continue with the restore? (yes/no): ").lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'.")


def ensure_users_exist(cursor):
    users = ['frank', 'admin', 'aura']
    password = 'P@ssw0rd1'
    for user in users:
        cursor.execute(f"CREATE USER IF NOT EXISTS '{user}'@'%' IDENTIFIED BY '{password}';")
        cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{user}'@'%' WITH GRANT OPTION;")
    cursor.execute("FLUSH PRIVILEGES;")


def drop_non_system_databases(cursor):
    system_databases = ['mysql', 'information_schema', 'performance_schema', 'sys']
    cursor.execute("SET foreign_key_checks = 0;")
    cursor.execute("SHOW DATABASES;")
    databases = cursor.fetchall()
    for (database,) in databases:
        if database not in system_databases:
            print(f"Dropping database: {database}")
            cursor.execute(f"DROP DATABASE IF EXISTS `{database}`;")
    cursor.execute("SET foreign_key_checks = 1;")


def restore_backup(restore_file):
    try:
        connection = MySQLdb.connect(**config)
        cursor = connection.cursor()

        drop_non_system_databases(cursor)
        ensure_users_exist(cursor)

        # Count total CREATE TABLE statements
        total_tables = 0
        with open(restore_file, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                if re.search(r'CREATE\s+TABLE', line, re.IGNORECASE):
                    total_tables += 1

        print(f"Total tables to restore: {total_tables}")

        start_time = time.time()
        restored_tables = 0

        cursor.execute("SET foreign_key_checks = 0")
        connection.autocommit(False)

        current_statement = []
        with open(restore_file, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                if line.strip().endswith(';'):
                    current_statement.append(line)
                    full_statement = ''.join(current_statement)
                    try:
                        cursor.execute(full_statement)
                        if re.search(r'CREATE\s+TABLE', full_statement, re.IGNORECASE):
                            restored_tables += 1
                            progress = (restored_tables / total_tables) * 100
                            elapsed_time = int(time.time() - start_time)
                            hours, remainder = divmod(elapsed_time, 3600)
                            minutes, seconds = divmod(remainder, 60)
                            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                            print(f"\rRestore Progress: {progress:.2f}% | Tables restored: {restored_tables}/{total_tables} | Time elapsed: {time_str}", end="", flush=True)
                    except MySQLdb.Error as e:
                        print(f"\nError executing statement: {e}")
                        print(f"Problematic statement: {full_statement[:100]}...")
                    current_statement = []
                else:
                    current_statement.append(line)

        cursor.execute("SET foreign_key_checks = 1")
        connection.commit()

        cursor.close()
        connection.close()

        print(f"\nBackup restored successfully from {restore_file}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 mysql-restore.py <backup_file>", file=sys.stderr)
        sys.exit(1)

    restore_file = sys.argv[1]

    if not os.path.exists(restore_file):
        print(f"ERROR: Backup file not found: {restore_file}", file=sys.stderr)
        sys.exit(1)

    missing = [v for v in ('MYSQL_LOCAL_USER', 'MYSQL_LOCAL_PASSWORD') if not os.getenv(v)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        print("Source ~/.claude/mysql.env before running this script.", file=sys.stderr)
        sys.exit(1)

    if print_config_and_prompt(restore_file):
        restore_backup(restore_file)
    else:
        print("Restore operation aborted.")
