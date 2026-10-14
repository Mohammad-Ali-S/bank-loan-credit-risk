"""Load the cleaned CSV into a local SQLite database."""
import os
import sqlite3
import pandas as pd

CLEAN_PATH = os.path.join("data", "processed", "loans_clean.csv")
DB_PATH = os.path.join("data", "loans.db")
SCHEMA_PATH = os.path.join("sql", "schema.sql")

def main():
    df = pd.read_csv(CLEAN_PATH)
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    df.to_sql("loans", conn, if_exists="append", index=False)
    count = conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
    print(f"Loaded {count} rows into {DB_PATH}")
    conn.close()

if __name__ == "__main__":
    main()
