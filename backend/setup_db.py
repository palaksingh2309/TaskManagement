"""
One-command database setup for TaskFlow Pro.
Creates the database (if missing), tables, and demo seed data.

Usage (from backend/ folder):
    python setup_db.py
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("MYSQL_HOST", "localhost")
PORT = int(os.getenv("MYSQL_PORT", "3306"))
USER = os.getenv("MYSQL_USER", "root")
PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DATABASE = os.getenv("MYSQL_DATABASE", "taskflow_pro")


def create_database():
    print(f"Connecting to MySQL at {HOST}:{PORT} as {USER}...")
    conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DATABASE}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        print(f"Database '{DATABASE}' is ready.")
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        create_database()
    except pymysql.err.OperationalError as e:
        print("\n[ERROR] Could not connect to MySQL.")
        print("  Make sure MySQL is installed and running.")
        print("  XAMPP: start MySQL from the XAMPP Control Panel.")
        print("  MySQL Installer: start the 'MySQL80' Windows service.")
        print(f"\n  Details: {e}")
        raise SystemExit(1) from e

    from app import create_app
    from app.extensions import db

    app = create_app()
    with app.app_context():
        db.create_all()
        print("Tables created.")

    print("Seeding demo data...")
    import subprocess, sys
    result = subprocess.run([sys.executable, "seed_db.py"], cwd=os.path.dirname(__file__))
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    print("\nSetup complete! Run: python run.py")
