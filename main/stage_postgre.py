import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from main.log import *

def upload_data_to_postgresql(dataframes_dict, script_name):
    # Define your PostgreSQL connection details
    db_config = {
        'user': 'postgres',
        'password': 'root',
        'host': 'localhost',
        'port': '5432',
        'database': 'postgres'
    }
    
    # Establish a connection to the PostgreSQL database
    try:
        connection = psycopg2.connect(**db_config)
        if connection:
            print("Connected to PostgreSQL database")
    except psycopg2.Error as err:
        print(f"Error: {err}")
        
    
    # Create SQLAlchemy engine
    engine = create_engine(f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
    logger.info(f"{engine} \n")
    
    # Specify the chunk size
    chunk_size = 5000  # Adjust the chunk size as needed
    
    # Create a cursor object
    cursor = connection.cursor()    

    for df_name, df in dataframes_dict.items():
        table_name = f"{script_name}_{df_name}"
        try:
            cursor.execute(f"TRUNCATE TABLE {table_name}")
            logger.info(f"Table {table_name} is truncated Successfully")
        except psycopg2.Error as e:
            logger.error(f"Error truncating table {table_name}: {e}")
            pass
        
        logger.info(f"Appending Data into {table_name}.....")
        # Write DataFrame to PostgreSQL table in chunks
        for i in range(0, len(df), chunk_size):
            df_chunk = df[i:i+chunk_size]
            print(df_chunk)
            df_chunk.to_sql(name=table_name, con=engine, if_exists='append', index=False)
            print(df_chunk)
            logger.info(f"{df_chunk.shape[0]} records appended")
        logger.info(f"Total {df.shape[0]} records are inserted into {table_name}\n")
    
    # Close the cursor and connection
    cursor.close()
    connection.close()
    logger.info(f"{db_config['host']} connection closed")
