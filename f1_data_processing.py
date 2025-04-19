# realtime_lap_analysis.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, explode
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType, ArrayType

def create_spark_session():
    """Creates and configures a SparkSession."""
    spark = SparkSession.builder \
        .appName("RealtimeLapAnalysis") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0") \
        .getOrCreate()
    # Set log level to WARN to reduce verbosity
    spark.sparkContext.setLogLevel("WARN")
    print("SparkSession created successfully.")
    return spark

def define_race_schema():
    """Defines the schema for the incoming race data from Kafka."""
    return StructType([
        StructField("current_lap", IntegerType()),
        StructField("cars", ArrayType(
            StructType([
                StructField("driver", StructType([
                    StructField("name", StringType())
                ])),
                StructField("last_lap", FloatType()) # Assuming last_lap time is a float
            ])
        ))
    ])

def process_lap_data(spark):
    """Reads race data from Kafka and prints lap times to the console in real-time."""
    race_schema = define_race_schema()
    print("Defined race schema.")

    # Read data from Kafka topic 'race'
    race_df = (spark
        .readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092") # Replace if your Kafka broker is elsewhere
        .option("subscribe", "race")                     # The Kafka topic to read from
        .option("startingOffsets", "latest")              # Start reading from the latest messages
        .option("failOnDataLoss", "false")                # Continue processing even if some data is lost
        .load()
    )

    print("Kafka source stream initialized.")

    # Process the incoming data
    processed_df = (race_df
        .selectExpr("CAST(value AS STRING) as json_data")
        .select(from_json(col("json_data"), race_schema).alias("race_data"))
        .filter(col("race_data").isNotNull()) # Ensure JSON parsing was successful
        .select("race_data.current_lap", col("race_data.cars").alias("all_cars"))
        .filter(col("all_cars").isNotNull()) # Ensure the 'cars' array exists
        .withColumn("car_info", explode(col("all_cars"))) # Explode the array of cars into individual rows
        # Filter out nulls after explode
        .filter(col("car_info").isNotNull() & col("car_info.driver.name").isNotNull() & col("car_info.last_lap").isNotNull())
        .select(
            col("current_lap"),
            col("car_info.driver.name").alias("driver_name"),
            col("car_info.last_lap").alias("lap_time")
        )
    )

    print("Data transformation defined.")

    # Print the lap times to the console in real-time
    query = (processed_df
        .writeStream
        .outputMode("append")
        .format("console")
        .option("truncate", "false")
        .start()
    )

    print("Streaming query started. Waiting for termination...")
    # Keep the application running while the query processes data
    query.awaitTermination()
    print("Streaming query terminated.")

if __name__ == "__main__":
    print("Starting F1 Realtime Lap Analysis script...")
    spark_session = None
    try:
        spark_session = create_spark_session()
        process_lap_data(spark_session)
    except Exception as e:
        print(f"An error occurred: {e}")
        # Optionally re-raise or log the exception details
        # import traceback
        # print(traceback.format_exc())
    finally:
        if spark_session:
            print("Stopping SparkSession.")
            spark_session.stop()
        print("Script finished.")