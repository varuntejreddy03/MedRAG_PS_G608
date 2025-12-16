"""Database migration script to add patient_name and patient_email columns."""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env file")
    exit(1)

print("Connecting to database...")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Add patient_name column
        try:
            print("Adding patient_name column...")
            conn.execute(text("ALTER TABLE patients ADD COLUMN patient_name VARCHAR"))
            conn.commit()
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"Warning: {e}")
        
        # Add patient_email column
        try:
            print("Adding patient_email column...")
            conn.execute(text("ALTER TABLE patients ADD COLUMN patient_email VARCHAR"))
            conn.commit()
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"Warning: {e}")
        
        print("SUCCESS: Migration completed!")
        
except Exception as e:
    print(f"ERROR: Migration failed: {e}")
    exit(1)
