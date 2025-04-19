from pyspark.sql import SparkSession
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("JDBCConnectionTest")

def test_jdbc_connection(spark, jdbc_url, jdbc_user, jdbc_password, jdbc_driver):
    """
    Tests the JDBC connection to a database.

    Args:
        spark: The SparkSession object.
        jdbc_url (str): The JDBC connection URL.
        jdbc_user (str): The username for the database.
        jdbc_password (str): The password for the database.
        jdbc_driver (str): The JDBC driver class name.

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    logger.info(f"Testing JDBC connection to: {jdbc_url}")
    try:
        # Attempt to read a simple query that should always succeed
        test_df = spark.read \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("user", jdbc_user) \
            .option("password", jdbc_password) \
            .option("driver", jdbc_driver) \
            .option("dbtable", "(SELECT 1) AS dummy") \
            .load()
        test_df.collect()  # Trigger the connection and data retrieval
        logger.info("JDBC connection successful")
        return True
    except Exception as e:
        logger.error(f"JDBC connection failed: {e}")
        logger.error(f"Error details: {e}")
        return False

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("JDBCConnectionTest") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.5.1").getOrCreate()

    jdbc_url = "jdbc:postgresql://localhost:5432/f1db"  # Replace with your JDBC URL
    jdbc_user = "postgres"  # Replace with your database username
    jdbc_password = "postgres"  # Replace with your database password
    jdbc_driver = "org.postgresql.Driver"  # Replace with your JDBC driver class name

    if test_jdbc_connection(spark, jdbc_url, jdbc_user, jdbc_password, jdbc_driver):
        print("Successfully connected to the database.")
    else:
        print("Failed to connect to the database. Check the logs for details.")

    spark.stop()