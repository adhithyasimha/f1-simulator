# f1_analytics.py
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from psycopg2.extras import RealDictCursor
import json

def connect_to_db():
    conn = psycopg2.connect(
        host="localhost",
        database="f1db",
        user="postgres",
        password="postgres",
        cursor_factory=RealDictCursor
    )
    return conn

def get_latest_race_status():
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT * FROM race_updates 
    ORDER BY id DESC 
    LIMIT 1
    """)
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return result

def get_driver_lap_times(driver_name):
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        id, current_lap, cars
    FROM 
        race_updates 
    WHERE 
        sector = 3
    ORDER BY 
        current_lap
    """)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    lap_times = []
    
    for row in results:
        cars = json.loads(row['cars']) if isinstance(row['cars'], str) else row['cars']
        for car in cars:
            if car['driver']['name'] == driver_name:
                lap_times.append({
                    'lap': row['current_lap'],
                    'time': car['last_lap']
                })
                break
    
    return lap_times

def plot_lap_time_comparison(driver1, driver2):
    driver1_data = get_driver_lap_times(driver1)
    driver2_data = get_driver_lap_times(driver2)
    
    d1_laps = [d['lap'] for d in driver1_data]
    d1_times = [d['time'] for d in driver1_data]
    
    d2_laps = [d['lap'] for d in driver2_data]
    d2_times = [d['time'] for d in driver2_data]
    
    plt.figure(figsize=(12, 6))
    plt.plot(d1_laps, d1_times, 'b-', label=driver1)
    plt.plot(d2_laps, d2_times, 'r-', label=driver2)
    plt.title(f'Lap Time Comparison: {driver1} vs {driver2}')
    plt.xlabel('Lap Number')
    plt.ylabel('Lap Time (seconds)')
    plt.legend()
    plt.grid(True)
    plt.savefig('lap_time_comparison.png')
    print(f"Lap time comparison saved to lap_time_comparison.png")

def display_race_summary():
    race_data = get_latest_race_status()
    
    if not race_data:
        print("No race data found in the database")
        return
    
    cars = json.loads(race_data['cars']) if isinstance(race_data['cars'], str) else race_data['cars']
    cars.sort(key=lambda x: x['position'])
    
    print(f"\nRace Summary - {race_data['circuit_name']}")
    print(f"Lap: {race_data['current_lap']}/{race_data['total_laps']}")
    print(f"Status: {race_data['race_status']}")
    print(f"Weather: {race_data['weather']}")
    print("\nDriver Standings:")
    print("=" * 50)
    print(f"{'Pos':<4}{'Driver':<20}{'Team':<15}{'Gap':<10}{'Status':<15}")
    print("-" * 50)
    
    for car in cars:
        gap = "LEADER" if car['position'] == 1 else f"+{car['gap_to_leader']:.3f}s"
        print(f"{car['position']:<4}{car['driver']['name']:<20}{car['driver']['team']:<15}{gap:<10}{car['race_status']:<15}")

if __name__ == "__main__":
    print("\nF1 Race Analytics Dashboard")
    print("=" * 50)
    
    display_race_summary()
    
    # Example of plotting lap time comparison between two drivers
    plot_lap_time_comparison("Max Verstappen", "Lewis Hamilton")