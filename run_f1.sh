#!/bin/bash
# run_f1_project.sh

# Check if PostgreSQL is running
pg_isready -h localhost -p 5432 -U postgres
if [ $? -ne 0 ]; then
    echo "PostgreSQL is not running. Please start it first."
    exit 1
fi

# Setup database
echo "Setting up database..."
python3 setup_database.py

# Start Kafka if it's not already running
echo "Checking Kafka status..."
nc -z localhost 9092
if [ $? -ne 0 ]; then
    echo "Starting Kafka..."
    # You might need to adjust these commands based on your Kafka installation
    $KAFKA_HOME/bin/zookeeper-server-start.sh -daemon $KAFKA_HOME/config/zookeeper.properties
    sleep 5
    $KAFKA_HOME/bin/kafka-server-start.sh -daemon $KAFKA_HOME/config/server.properties
    sleep 10
fi

# Start Spark data processing in the background
echo "Starting Spark data processing..."
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,org.postgresql:postgresql:42.5.1 f1_data_processing.py &
SPARK_PID=$!
sleep 10  # Give Spark time to initialize

# Run qualifying simulation
echo "Running qualifying simulation..."
python3 qualifying.py

# Run race simulation 
echo "Running race simulation..."
python3 race_simulation.py

# Generate analytics
echo "Generating analytics..."
python3 f1_analytics.py

# Cleanup - kill Spark job
kill $SPARK_PID

echo "F1 Race Simulation and Analytics complete!"