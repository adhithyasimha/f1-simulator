# setup_database.py
import psycopg2

def setup_database():
    # Connect to default postgres database to create our F1 database
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create the F1 database if it doesn't exist
    cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'f1db'")
    if not cursor.fetchone():
        cursor.execute("CREATE DATABASE f1db")
    
    cursor.close()
    conn.close()
    
    # Connect to the F1 database and create tables
    conn = psycopg2.connect(
        host="localhost",
        database="f1db",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    
    # Create qualifying sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qualifying_sessions (
        id SERIAL PRIMARY KEY,
        session_name VARCHAR(5),
        circuit_name VARCHAR(100),
        weather VARCHAR(50),
        timestamp VARCHAR(50),
        drivers JSON,
        processing_time TIMESTAMP
    )
    """)
    
    # Create grid positions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grid_positions (
        id SERIAL PRIMARY KEY,
        circuit_name VARCHAR(100),
        timestamp VARCHAR(50),
        grid_positions JSON,
        pole_time FLOAT,
        processing_time TIMESTAMP
    )
    """)
    
    # Create race updates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS race_updates (
        id SERIAL PRIMARY KEY,
        timestamp VARCHAR(50),
        circuit_name VARCHAR(100),
        current_lap INT,
        total_laps INT,
        race_status VARCHAR(50),
        weather VARCHAR(50),
        safety_car BOOLEAN,
        drs_enabled BOOLEAN,
        sector INT,
        cars JSON,
        fastest_lap JSON,
        processing_time TIMESTAMP
    )
    """)
    
    # Create car telemetry table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS race_car_telemetry (
        id SERIAL PRIMARY KEY,
        timestamp VARCHAR(50),
        circuit_name VARCHAR(100),
        current_lap INT,
        race_status VARCHAR(50),
        sector INT,
        cars JSON,
        processing_time TIMESTAMP
    )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Database setup complete!")

if __name__ == "__main__":
    setup_database()