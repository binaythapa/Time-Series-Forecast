import pandas as pd
import mysql.connector
import sys 
from sqlalchemy import create_engine
from main.log import *
from main.select_insert_update_logic import *
#from scripts.finale.test import *

def upload_data_to_mysql(dataframes_dict, script_name,append=False):

    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.000')
    # Define your MySQL connection details
    db_config = {
        'user': 'root',
        'password': "root",
        'host': 'localhost',
        'database':'mystyle'  
        #,'port': '3306'
    }
    # Establish a connection to the MySQL database
    try:
        connection = mysql.connector.connect(**db_config)
        #connection = mysql.connector.connect(host='localhost',user='root',password='eBIwgz6vSto4qAi','database':'stg_pepco')
        if connection.is_connected():
            print("Connected to MySQL database")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        
    
  
    # Create SQLAlchemy engine
    #engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
    engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")
    logger.info(f"{engine} \n")
    
    #cursor = connection.cursor()
    
    # Specify the chunk size
    chunk_size = 10000  # Adjust the chunk size as needed
    
    # Create a cursor object
    cursor = connection.cursor()    

    for df_name, df in dataframes_dict.items():
        table_name = f"{script_name}_{df_name}"
        if not append:                
                try:
                    cursor.execute(f"TRUNCATE TABLE {db_config['database']}.{table_name}")
                    logger.info(f"Table {table_name} truncated successfully")
                except Exception as e:
                    logger.error(f"Unable to truncate {db_config['database']}.{table_name}: {e}")
                    #sys.exit()
        
        
        #logger.info(f"Appending Data into {db_config['database']}.{table_name}.....")
        # Write DataFrame to MySQL table in chunks
        for i in range(0, len(df), chunk_size):
            df_chunk = df[i:i+chunk_size]            
            df_chunk.to_sql(name=table_name, con=engine, if_exists='append', index=False)
            logger.info(f"{df_chunk.shape[0]} records appended")
        logger.info(f"Total {df.shape[0]} records are inserted into {table_name}\n")


        #table_name = 'data_count_log'
        data_count = df.shape[0]  # Assuming df_chunk is a pandas DataFrame
        

        insert_query = f'''
            INSERT INTO {db_config['database']}.data_count_log (script_name, table_name, data_count, date)
            VALUES (%s, %s, %s, %s)
            '''

# Assuming script_name is defined elsewhere
        execute_insert_query(insert_query, script_name, table_name, data_count, date)
    
        # Close the cursor and connection
    cursor.close()
    connection.close()
    logger.info(f"{db_config['host']} connection closed")
    
    return df.shape[0]