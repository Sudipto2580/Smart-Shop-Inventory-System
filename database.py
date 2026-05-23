import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "inventory.db")

def get_connection():
    return sqlite3.connect(DB_NAME)