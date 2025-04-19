from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, explode
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType, ArrayType
import psycopg2

def create_spark_session():
    """Creates and configures a SparkSession."""
    spark = SparkSession.builder \
        .appName("RealtimeLapAnalysis") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0,org.postgresql:postgresql:42.5.1") \
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
                    StructField("name", StringType()),
                    StructField("number", IntegerType())
                ])),
                StructField("last_lap", FloatType())
            ])
        ))
    ])

def truncate_postgres_table():
    """Truncates the f1_lap_times table in PostgreSQL."""
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="f1db",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE f1_lap_times;")
        conn.commit()
        print("Table f1_lap_times truncated successfully.")
    except psycopg2.Error as e:
        print(f"Error truncating table: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

def write_to_postgres(batch_df, batch_id):
    """Writes the DataFrame batch to PostgreSQL in the new table."""
    try:
        batch_df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://localhost:5432/f1db")\
            .option("dbtable", "f1_lap_times")\
            .option("user", "postgres")\
            .option("password", "postgres")\
            .option("driver", "org.postgresql.Driver")\
            .mode("append")\
            .save()
        print(f"Batch {batch_id} written to f1_lap_times.")
    except Exception as e:
        print(f"Error writing batch {batch_id} to f1_lap_times: {e}")

def process_lap_data(spark):
    """Reads race data from Kafka and writes lap times with driver number to PostgreSQL in real-time."""
    race_schema = define_race_schema()
    print("Defined race schema.")

    # Read data from Kafka topic 'race'
    race_df = (spark
        .readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", "race")
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )

    print("Kafka source stream initialized.")

    # Process the incoming data
    processed_df = (race_df
        .selectExpr("CAST(value AS STRING) as json_data")
        .select(from_json(col("json_data"), race_schema).alias("race_data"))
        .filter(col("race_data").isNotNull())
        .select("race_data.current_lap", col("race_data.cars").alias("all_cars"))
        .filter(col("all_cars").isNotNull())
        .withColumn("car_info", explode(col("all_cars")))
        .filter(col("car_info").isNotNull() & col("car_info.driver.name").isNotNull() & col("car_info.driver.number").isNotNull() & col("car_info.last_lap").isNotNull())
        .select(
            col("current_lap"),
            col("car_info.driver.name").alias("driver_name"),
            col("car_info.driver.number").alias("driver_number"),
            col("car_info.last_lap").alias("lap_time")
        )
    )

    print("Data transformation defined.")

    # Write the processed data to PostgreSQL in batches
    query = (processed_df
        .writeStream
        .outputMode("append")
        .foreachBatch(write_to_postgres)
        .option("checkpointLocation", "/tmp/checkpoint/f1_lap_times") # New checkpoint location
        .trigger(processingTime="5 seconds")
        .start()
    )

    print("Streaming query started. Waiting for termination...")
    query.awaitTermination()
    print("Streaming query terminated.")

if __name__ == "__main__":
    print("Starting F1 Realtime Lap Analysis script...")
    # Truncate the PostgreSQL table before starting the Spark job
    truncate_postgres_table()
    spark_session = None
    try:
        spark_session = create_spark_session()
        process_lap_data(spark_session)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if spark_session:
            print("Stopping SparkSession.")
            spark_session.stop()
        print("Script finished.")