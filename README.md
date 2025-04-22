# 🏎️ Kafka F1 Race Simulator - Singapore GP Edition 🏁

This isn't just another data project - it's a ticket to experience the thrill of the Singapore night race through the lens of real-time event processing!

This project lets you recreate the magic of racing under the lights at Marina Bay, with all the humidity, tight corners, and concrete walls that make Singapore one of the most demanding circuits on the calendar.

The simulation runs in two heart-pounding stages:

- **Qualifying Session:** ⏱️  
  A separate script (`qualifying.py`) simulates the intense battle for pole position under the Singapore lights, calculates lap times, and publishes the final grid positions to Kafka on the `grid` topic.

- **Race Simulation:** 🏁  
  The race simulation script (`race_simulation.py`) consumes the grid data from Kafka, then brings the full 61-lap Marina Bay street circuit to life! Every overtake attempt, safety car deployment, and pit stop strategy is broadcast to the `race` Kafka topic.

- **Real-time Data Processing:** 📊  
  The Spark streaming application (`f1_data_processing.py`) processes race data from Kafka in real-time, extracts lap times and driver information, and stores it in a PostgreSQL database for analytics.

- **Live Race Analytics:** 📈  
  The Streamlit dashboard (`f1_analytics.py`) provides real-time visualization of race standings, lap time comparisons, and race status updates directly from the PostgreSQL database.

---

## How This Magic Works

### Qualifying Stage

#### Qualifying Session
- Drivers push their limits setting lap times through Singapore's 23 corners, with results determined by driver skill, team performance, tire choices, and that dash of racing luck.
- The script sends live qualifying messages to the Kafka topic `quali` as drivers battle for the perfect hot lap.
- After the checkered flag, the final grid positions and data are published to the Kafka topic `grid`.

### Race Simulation Stage

#### Grid Consumption
- The script consumes the grid message from the `grid` topic using a Kafka consumer.
- The grid data puts our drivers in position on Marina Bay's starting straight, ready for the only night race start on the calendar!

#### Race Mechanics & Features

- **Race Conditions:**
  - **Race Statuses:**  
    The simulator handles different flags - from green flag racing to the safety car periods (practically guaranteed in Singapore!).
  - **Weather Conditions:**  
    Currently set to typical Singapore humidity, but can handle the occasional tropical downpour that makes this street circuit even more treacherous.

- **Tire Compounds:**
  - Three types of tires to manage: Soft, Medium, and Hard - crucial in Singapore's punishing conditions.
  - Each compound affects performance differently - just like the real race where tire strategy often makes the difference.

- **Team & Driver Performance:**
  - Drivers have attributes like skill, wet skill, aggression, and tire management - all tested to the limit on this physical track.
  - Teams have performance factors per sector - some excel in Singapore's tight final sector while others shine in the few straights.

- **Lap and Sector Time Calculations:**
  - 61 laps around Singapore's punishing street circuit, each divided into 3 sectors.
  - Sector times computed with consideration for Singapore's unique challenges - the hard braking zones, the bumpy surface, and the unforgiving walls.

- **Pit Stops:**
  - Teams must decide when to pit based on tire wear and the ever-present threat of safety cars.
  - Pit stops can make or break a race in Singapore, where track position is king!

- **Incidents and Safety Car Deployment:**
  - Random incidents may occur - and just like the real Singapore GP, safety cars appear with remarkable frequency.
  - Watch out for the notorious Turn 7 and the final chicane - they've claimed many F1 casualties over the years.

- **Overtakes and DRS:**
  - Overtaking is notoriously difficult in Singapore - our simulation captures this challenge!
  - DRS zones provide rare overtaking opportunities, with success rates reflecting the circuit's tight confines.

- **Fastest Lap and Final Classification:**
  - Fastest lap tracking rewards the brave driver who pushes when everyone else is managing tires.
  - Final classification with points that could swing the championship!

- **Real-Time Updates:**
  - Live race updates flow to the `race` Kafka topic as the drama unfolds under the Singapore lights.

### Data Processing Stage

- **Spark Streaming:**
  - A PySpark application consumes race data from the `race` Kafka topic in real-time.
  - The application processes and transforms the data, extracting key metrics like lap times and driver performance.
  - Processed data is continuously written to a PostgreSQL database, providing a solid foundation for analytics.

### Analytics Dashboard

- **Streamlit Visualization:**
  - A real-time Streamlit dashboard provides an interactive view of the race as it unfolds.
  - Features include:
    - Current race status and conditions
    - Live driver standings with gaps to the leader
    - Lap-by-lap time comparison between selected drivers
    - Race progress tracking
  - The dashboard refreshes automatically to show the latest race data from PostgreSQL.

---

## Setup & Installation

### Prerequisites

- **Apache Kafka:**  
  Install Kafka locally or use Docker.

  **To start Kafka manually:**

  1. **Start Zookeeper:**
     ```bash
     bin/zookeeper-server-start.sh config/zookeeper.properties
     ```
  2. **Start Kafka Broker:**
     ```bash
     bin/kafka-server-start.sh config/server.properties
     ```

- **Apache Spark:**
  Install Spark 3.x locally or use Docker.

- **PostgreSQL:**
  Install PostgreSQL locally or use Docker.

  **Create the required database and tables:**
  ```sql
  CREATE DATABASE f1db;
  
  -- Connect to the f1db database
  \c f1db
  
  -- Create table for storing lap times
  CREATE TABLE f1_lap_times (
    id SERIAL PRIMARY KEY,
    current_lap INT,
    driver_name VARCHAR(100),
    driver_number INT,
    lap_time FLOAT
  );
  
  -- Create table for race updates
  CREATE TABLE race_updates (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    circuit_name VARCHAR(100),
    current_lap INT,
    total_laps INT,
    race_status VARCHAR(50),
    weather VARCHAR(50),
    cars JSONB
  );
  ```

- **Python 3.8+**

- **Python Dependencies:**  
  Install required libraries:
  ```bash
  pip install kafka-python pyspark psycopg2 streamlit pandas matplotlib
  ```

### Creating Kafka Topics

Run these commands in your Kafka installation directory to create the required topics:

```bash
# Create the topic for qualifying messages
kafka-topics.sh --create --topic quali --bootstrap-server localhost:9092

# Create the topic for sending the final grid
kafka-topics.sh --create --topic grid --bootstrap-server localhost:9092

# Create the topic for live race updates
kafka-topics.sh --create --topic race --bootstrap-server localhost:9092
```

## Running the Simulation

### Run Qualifying Script:
First, execute the qualifying script to see who'll claim pole position at Marina Bay:

```bash
python qualifying.py
```

### Run Race Simulation:
After qualifying is complete, it's time for the Singapore night race to begin:

```bash
python race_simulation.py
```

The race simulation script will consume the grid message, simulate the entire Singapore Grand Prix, and send live updates to the `race` topic.

### Run Data Processing Pipeline:
Start the Spark streaming job to process race data and write to PostgreSQL:

```bash
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,org.postgresql:postgresql:42.5.1 f1_data_processing.py
```

### Launch Analytics Dashboard:
Start the Streamlit dashboard to visualize the race in real-time:

```bash
streamlit run f1_analytics.py
```

Access the dashboard in your browser at http://localhost:8501

---

## Data Flow Architecture

```
                 ┌───────────────┐
                 │  qualifying.py│
                 └───────┬───────┘
                         │
                         ▼
      ┌───────────────────────────────┐
      │     Kafka Topic: "quali"      │
      └───────────────────────────────┘
                         │
                         │
                         ▼
      ┌───────────────────────────────┐
      │     Kafka Topic: "grid"       │
      └───────────────────────────────┘
                         │
                         │
                         ▼
                 ┌───────────────┐
                 │race_simulation│
                 └───────┬───────┘
                         │
                         ▼
      ┌───────────────────────────────┐
      │     Kafka Topic: "race"       │
      └───────────────────────────────┘
                         │
                         ▼
       ┌─────────────────────────────┐
       │   f1_data_processing.py     │
       │      (PySpark Job)          │
       └─────────────┬───────────────┘
                     │
                     ▼
         ┌─────────────────────┐
         │   PostgreSQL DB     │
         │   (f1db)            │
         └─────────┬───────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │   f1_analytics.py   │
         │  (Streamlit App)    │
         └─────────────────────┘
```

---

Enjoy exploring real-time event processing with Apache Kafka, Spark, and Streamlit while experiencing the thrills of the Singapore GP - where racing meets the night, and data engineering meets F1!

P.S. Don't be surprised if the safety car makes multiple appearances - it's a Singapore tradition after all!
