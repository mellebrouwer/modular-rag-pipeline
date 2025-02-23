import os
import pandas as pd
import sqlite3
from pathlib import Path

def create_canteen_db():
    # Define paths
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / "data" / "bank_info" / "canteen_data.csv"
    db_path = base_dir / "data" / "bank_info" / "canteen_data.db"
    
    # Ensure the directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read CSV file
    df = pd.read_csv(csv_path)
    
    # Convert timestamp strings to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Create SQLite database and table
    with sqlite3.connect(str(db_path)) as conn:
        # Create transactions table
        df.to_sql('transactions', conn, index=False, if_exists='replace')
        
        # Create indices for better query performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_user ON transactions(User)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON transactions(Timestamp)')
        
        # Verify the data
        row_count = conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
        print(f"Successfully created database at {db_path}")
        print(f"Inserted {row_count} rows")
        
        # Show sample query
        print("\nSample query result (last 5 transactions):")
        query = "SELECT * FROM transactions ORDER BY Timestamp DESC LIMIT 5"
        sample = pd.read_sql_query(query, conn)
        print(sample)

if __name__ == "__main__":
    create_canteen_db()
