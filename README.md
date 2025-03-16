# 🏎️ Kafka F1 Race Simulator - Singapore GP Edition 🏁

This isn't just another data project - it's a ticket to experience the thrill of the Singapore night race through the lens of real-time event processing!

This project lets you recreate the magic of racing under the lights at Marina Bay, with all the humidity, tight corners, and concrete walls that make Singapore one of the most demanding circuits on the calendar.

The simulation runs in two heart-pounding stages:

- **Qualifying Session:** ⏱️  
  A separate script (`qualifying.py`) simulates the intense battle for pole position under the Singapore lights, calculates lap times, and publishes the final grid positions to Kafka on the `grid` topic.

- **Race Simulation:** 🏁  
  The race simulation script (`race_simulation.py`) consumes the grid data from Kafka, then brings the full 61-lap Marina Bay street circuit to life! Every overtake attempt, safety car deployment, and pit stop strategy is broadcast to the `race` Kafka topic.

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

- **Python 3.8+**

- **Python Dependencies:**  
  Install required libraries:
  ```bash
  pip install kafka-python
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

---

Enjoy exploring real-time event processing with Apache Kafka while experiencing the thrills of the Singapore GP - where racing meets the night, and Kafka meets F1!

P.S. Don't be surprised if the safety car makes multiple appearances - it's a Singapore tradition after all!
