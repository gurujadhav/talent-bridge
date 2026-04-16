import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

def get_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found! Check your .env file.")
    return psycopg.connect(db_url, autocommit=True)
