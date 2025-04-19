import streamlit as st
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from psycopg2.extras import RealDictCursor
import json
import time

# --- Database Connection ---
def connect_to_db():
    conn = psycopg2.connect(
        host="localhost",
        database="f1db",
        user="postgres",
        password="postgres",
        cursor_factory=RealDictCursor
    )
    return conn

# --- Data Fetching Functions ---
@st.cache_data(ttl=5)  # Cache for 5 seconds for near real-time updates
def get_latest_race_status_streamlit():
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

@st.cache_data(ttl=5)
def get_driver_lap_times_streamlit(driver_number):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        current_lap, lap_time
    FROM
        f1_lap_times
    WHERE
        driver_number = %s
    ORDER BY
        current_lap
    """, (driver_number,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    lap_times = pd.DataFrame(results)
    return lap_times

@st.cache_data(ttl=3600)  # Cache driver names for longer
def get_driver_name_streamlit(driver_number):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT DISTINCT driver_name
    FROM f1_lap_times
    WHERE driver_number = %s
    """, (driver_number,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['driver_name'] if result else f"Driver #{driver_number}"

@st.cache_data(ttl=60)  # Cache for a minute as driver numbers might not change frequently
def get_distinct_driver_numbers():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT DISTINCT driver_number
    FROM f1_lap_times
    ORDER BY driver_number
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row['driver_number'] for row in results]

# --- Streamlit App ---
st.title("Real-time F1 Race Analytics")

# Sidebar for Driver Selection
st.sidebar.header("Driver Comparison")
available_drivers = get_distinct_driver_numbers()
selected_drivers = st.sidebar.multiselect("Select drivers for lap time comparison:", available_drivers, default=[1, 44] if 1 in available_drivers and 44 in available_drivers and len(available_drivers) >= 2 else available_drivers[:min(2, len(available_drivers))])

# Real-time Race Summary
st.subheader("Latest Race Status")
race_status = get_latest_race_status_streamlit()
if race_status:
    st.write(f"**Circuit:** {race_status['circuit_name']}")
    st.write(f"**Lap:** {race_status['current_lap']}/{race_status['total_laps']}")
    st.write(f"**Status:** {race_status['race_status']}")
    st.write(f"**Weather:** {race_status['weather']}")

    st.subheader("Driver Standings")
    cars_data = json.loads(race_status['cars']) if isinstance(race_status['cars'], str) else race_status['cars']
    standings_df = pd.DataFrame(cars_data)
    standings_df = standings_df.sort_values(by='position')
    standings_df['Gap'] = standings_df.apply(lambda row: 'LEADER' if row['position'] == 1 else f"+{row['gap_to_leader']:.3f}s", axis=1)
    standings_df = standings_df[['position', 'driver', 'driver.number', 'driver.team', 'Gap', 'race_status']]
    standings_df.columns = ['Pos', 'Driver', 'Number', 'Team', 'Gap', 'Status']
    st.dataframe(standings_df, hide_index=True)
else:
    st.warning("No race data available.")

# Real-time Lap Time Comparison Plot
if selected_drivers:
    st.subheader("Lap Time Comparison")
    fig, ax = plt.subplots(figsize=(12, 6))
    for driver_number in selected_drivers:
        lap_data = get_driver_lap_times_streamlit(driver_number)
        if not lap_data.empty:
            driver_name = get_driver_name_streamlit(driver_number)
            ax.plot(lap_data['current_lap'], lap_data['lap_time'], marker='o', linestyle='-', linewidth=1, markersize=3, label=f"#{driver_number} {driver_name}")
        else:
            st.warning(f"No lap time data found for driver number {driver_number}.")

    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time (seconds)")
    ax.set_title("Lap Time Comparison")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
else:
    st.info("Select drivers in the sidebar to see lap time comparison.")

# --- Run the Streamlit App ---
if __name__ == "__main__":
    pass # Streamlit will handle the execution