import os
import time
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Database credentials (hardcoded)
DB_HOST = "mariadb"
DB_USER = "user"
DB_PASSWORD = "password"
DB_NAME = "files_db"

def connect_db(retries=5, delay=10):
    """Connect to MariaDB with retry logic and enforce compatible collation."""
    for i in range(retries):
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4",  # Forces a compatible character set
                collation="utf8mb4_general_ci"  # Avoids unsupported MySQL 8 collations
            )
            if conn.is_connected():
                print("Connected to MariaDB")
                return conn
        except Error as e:
            print(f"Database connection failed (attempt {i+1}/{retries}): {e}")
            time.sleep(delay)
    print("Failed to connect after multiple retries. Exiting.")
    exit(1)

def create_table():
    """Create the database table if it doesn't exist."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255),
            path TEXT,
            size BIGINT,
            format VARCHAR(50),
            creation_date DATETIME,
            modification_date DATETIME
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def scan_files(directory="/data"):
    """Scan files and insert metadata into the database."""
    conn = connect_db()
    cursor = conn.cursor()

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            stat = os.stat(file_path)
            format_ = file.split('.')[-1] if '.' in file else 'unknown'

            try:
                cursor.execute("""
                    INSERT INTO files (filename, path, size, format, creation_date, modification_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    file,
                    file_path,
                    stat.st_size,
                    format_,
                    datetime.fromtimestamp(stat.st_ctime),
                    datetime.fromtimestamp(stat.st_mtime),
                ))
            except Error as e:
                print(f"Failed to insert {file_path}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("File scanning completed.")

if __name__ == "__main__":
    create_table()
    scan_files()
