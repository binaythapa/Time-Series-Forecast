import os
import sys
import shutil
import datetime
from datetime import timedelta
import snowflake.connector
import pymssql
import pandas as pd
from pandasql import sqldf
import json
import pyodbc
from main.log import *

import traceback
import re
import mysql.connector
import sqlite3
import numpy as np
import psycopg2
from psycopg2 import OperationalError
from sqlalchemy import create_engine


    
# Get the current date in a specific format (e.g., YYYYMMDD)
current_date = datetime.datetime.now().strftime("%Y%m%d")

def log(msg):
  logger.info(f"Executing {msg}.py.........................")
    
 
class db_connector:
    def __init__(self, json_filename):
        self.json_filename = json_filename

    def load_credentials_from_json(self, database_key):
        with open(self.json_filename, 'r') as json_file:
            credentials = json.load(json_file)
        return credentials.get(database_key, {})
    
    def oracle(self, database_key):
        logger.info(f"Connecting to Oracle database: {database_key}")
        try:
            credentials = self.load_credentials_from_json(database_key)

            if not credentials:
                logger.warning(f"No credentials found for database key: {database_key}")
                sys.exit(1)        

            # Construct the connection string
            dsn = cx_Oracle.makedsn(credentials["host"], int(credentials["port"]), sid=credentials["sid"])            
            connection = cx_Oracle.connect(user=credentials["username"], password=credentials["password"], dsn=dsn, mode=cx_Oracle.SYSDBA)
            logger.info(f"Connected to Oracle database {database_key}\n{' ' * 34} host:{credentials['host']}\n{' ' * 34} user:{credentials['username']}\n{' ' * 34} SID:{credentials['sid']}")
            return connection
        
        except Exception as e:
            logger.error("Error connecting to the Oracle database:", e)
            sys.exit(1)
    
    def postgres(self, database_key):
        logger.info(f"Connecting to database: {database_key}")
        try:
            connection_string = self.load_credentials_from_json(database_key)

            if not connection_string:
                logger.warning(f"No credentials found for database key: {database_key}")
                sys.exit(1)           
            
            connection = psycopg2.connect(**connection_string)            
            logger.info(f"Connected to database {database_key}\n"
            f"{' ' * 34} host: {connection_string['host']}\n"
            f"{' ' * 34} user: {connection_string['user']}\n"
            f"{' ' * 34} database: {connection_string.get('dbname', 'N/A')}\n"
            f"{' ' * 34} port: {connection_string.get('port', 'N/A')}")

            return connection
        except Exception as e:
            logger.error("Error connecting to the database:", e)
            sys.exit(1)


    def mysql(self,database_key):
      logger.info(f"Connecting to database: {database_key}")
      try:
          connection_string = self.load_credentials_from_json(database_key)

          if not connection_string:
            logger.warning(f"No credentials found for database key: {database_key}")
            sys.exit(1)  
         
          connection = mysql.connector.connect(**connection_string)
          logger.info(f"Connected to database {database_key}\n{' ' * 34} server:{connection_string['host']}\n{' ' * 34} user:{connection_string['user']}\n{' ' * 34} database:{connection_string.get('database','N/A')}")

          return connection
      except Exception as e:
          logger.error("Error connecting to the database:", e)
          sys.exit(1)

        
    def mssql(self, database_key):
      logger.info(f"Connecting to database : {database_key}")
      try:
        credentials = self.load_credentials_from_json(database_key)  

        if not credentials:
            logger.warning(f"No credentials found for database key: {database_key}")
            sys.exit(1)

        # Attempt to connect using server type
        try:
            
            connection_string = {
                'server': credentials["server"],
                'database': credentials.get("database"),
                'user': credentials["username"],
                'password': credentials["password"]
            }
            connection = pymssql.connect(**connection_string)           
            logger.info(f"Connected to database {database}\n{' ' * 34} server: {credentials['server']}\n{' ' * 34} user: {credentials['username']}\n{' ' * 34} database: {credentials.get('database', 'N/A')}")
            
        except KeyError:            
            try:
                connection_string = f'DSN={credentials["DSN"]};USER={credentials["USER"]}'               
                connection = pyodbc.connect(connection_string)
                logger.info(f"Connected to database {database_key}\nuser: {credentials['USER']}")

            except KeyError:               
                connection_string = f'DRIVER={{SQL Server}};SERVER={credentials["server"]};DATABASE={credentials["database"]};Trusted_Connection= yes;'
                connection=pyodbc.connect(connection_string)
                logger.info(f"Connected to database {database_key}\ndatabase: {credentials['database']}")
            except KeyError as e:
                logger.warning(f"No valid connection details found in credentials for database key: {database_key}")
                sys.exit(1)

        return connection

      except Exception as e:
        logger.error("Error connecting to the database:", e)
        sys.exit(1)            
    
    def snowflake(self, database_key):
        logger.info(f"Connecting to database : {database_key}")
        try:
            credentials = self.load_credentials_from_json(database_key)

            if not credentials:
                logger.warning(f"No credentials found for database key: {database_key}")             
                sys.exit(1)              
           
            connection = snowflake.connector.connect(**credentials)            
            logger.info(f"Connected to database {database_key}\n{' ' * 34} account:{credentials['account']}\n{' ' * 34} user:{credentials['user']}\n{' ' * 34} database:{credentials['database']}\n{' ' * 34} warehouse:{credentials['warehouse']}")
            return connection
        except Exception as e:
            logger.error("Error connecting to the database:", e)
            sys.exit(1)           
            
    def sqlite(self,script_name):
      logger.info(f"Connecting to SQLite database: f'{script_name}.db")
      sqlite_folder = os.path.join(os.getcwd(), 'sqlite')
      database_path = os.path.join(sqlite_folder, f'{script_name}.db')
    
      try:      
        db_directory = os.path.dirname(database_path)
        if not os.path.exists(db_directory):
            logger.info(f"Creating directory: {db_directory}")
            os.makedirs(db_directory)
        
        conn = sqlite3.connect(database_path)        
        logger.info(f"Connected to SQLite database: {database_path}")        
        return conn
    
      except Exception as e:
        logger.error("Error connecting to the SQLite database:", e)
        sys.exit(1)
 
      
    def create_sqlite_tables(self, connection, table_dataframes):
     try:      
        table_info ="\n+--------------------------+---------------------------+\n"
        table_info += "|        Table Name        |            Row Count      |\n"
        table_info += "+--------------------------+---------------------------+\n"        
        for table_name, dataframe in table_dataframes.items():           
            dataframe.to_sql(table_name, connection, index=False, if_exists='replace')           
            row_count = len(dataframe)           
            table_info += f"| {table_name.ljust(25)} | {str(row_count).ljust(25)} |\n"        
        table_info += "+--------------------------+---------------------------+\n"        
        logger.info(table_info)       
        connection.commit()        
        logger.info("Tables created successfully.")
        
     except Exception as e:        
        logger.error(f"Error creating tables: {e}")       
        sys.exit(1)
     finally:        
        pass
                
    def execute_query_and_fetch_data(self, connection, query, query_parameters=None):
      cursor = None

      try:        
            cursor = connection.cursor()
        #with connection.cursor() as cursor:
            if query_parameters is not None:                               
                logger.info(f"Data Fetching from {connection} \nParameters: {query_parameters}\n{query}")
                cursor.execute(query, query_parameters)                
            else:
                logger.info(f"Data Fetching from {connection} \n{query}")
                cursor.execute(query)
            try:
                query_results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                query_results = [list(row) for row in query_results]
                df = pd.DataFrame(query_results, columns=columns)

                logger.info(f"Data Fetched successfully from {connection}")
                return df
            except:
                pass
      except Exception as e:
        logger.error(f"Error executing query: {e}\n{traceback.format_exc()}")
        raise RuntimeError("Error executing query") from e

      finally:
        if cursor:
            try:
                cursor.close()
                logger.info("Cursor closed.")
            except Exception as e:
                logger.error(f"Error closing cursor: {e}")
        if connection:
            try:
              connection.close()
              logger.info(f"Connection closed from {connection} database")
              
            except Exception as e:
              logger.error(f"Error closing connection: {e}")  

# Example usage:
# result_df = execute_query_and_fetch_data(connection, your_query, query_parameters)
         
       
    def close_connection(self,connection):
      try:
        if connection:
            connection.close()
            logger.info(f"Connection closed from {connection} database")
      except Exception as e:
        logger.error(f"Error closing connection: {e}")        
      
def move_files(source_directory, destination_directory, starts_with):
    logger.info(f"Moving Files \n{' ' * 34}Source    : {source_directory} \n{' ' * 34}Destination: {destination_directory} \n{' ' * 34}Files starts_with: {starts_with}")
    
    # List only files in the source directory that start with the specified prefix
    filtered_files = [
        f for f in os.listdir(source_directory) 
        if f.startswith(starts_with) and os.path.isfile(os.path.join(source_directory, f))
    ]

    if not filtered_files:
        logger.info("No files to move.\n {' ' * 34}")
        return

    # Move the filtered files to the destination directory
    for file in filtered_files:
        source_path = os.path.join(source_directory, file)
        destination_path = os.path.join(destination_directory, file)
        shutil.move(source_path, destination_path)
        logger.info(f"File {file} moved successfully.\n {' ' * 34}")

             

def write_to_excel(data, file_name=None, sheet_name=None):  
    logger.info(f"Creating Excel File \n{' ' * 34}File Name: {file_name} \n{' ' * 34}Sheet Name: {sheet_name}") 
    file_name = str(file_name)

    if isinstance(data, pd.DataFrame):
        # Single DataFrame, write to the specified sheet
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)            
            logger.info(f" Excel file created successfully\n {' ' * 34}")
			
    elif isinstance(data, list) and all(isinstance(df, pd.DataFrame) for df in data):
        # List of DataFrames, write each DataFrame to a separate sheet
        if not sheet_name or len(sheet_name) != len(data):
            raise ValueError("Provide a list of sheet names for each DataFrame.")
            
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            for i, (df, sheet_name) in enumerate(zip(data, sheet_name)):
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            logger.info(f" Excel file created successfully\n {' ' * 34}")
    else:
        logger.error(f"An error occurred: {e}")
# Example Usage:
# To write a single DataFrame to a sheet
# write_to_excel(df, 'output', sheet_name='Sheet1')

# To write multiple DataFrames to separate sheets
# write_to_excel([df1, df2], 'output',sheet_name= [name1, name2])


def write_to_csv(data, file_name=None):
    logger.info(f"Creating csv File \n{' ' * 34}File Name: {file_name}")  
    file_name = str(file_name)

    if isinstance(data, pd.DataFrame):
        # Single DataFrame, write to CSV
        data.to_csv(file_name, index=False)
        logger.info(f" CSV File created successfully\n {' ' * 34}")
			
    elif isinstance(data, list) and all(isinstance(df, pd.DataFrame) for df in data):
        # List of DataFrames, write each DataFrame to a separate CSV file
        for i, df in enumerate(data):
            df.to_csv(f"{file_name}_{i + 1}.csv", index=False)
        logger.info(f" CSV File created successfully\n {' ' * 34}")
    else:
        raise ValueError("Unsupported data type. Provide either a single DataFrame or a list of DataFrames.")


def run_sql(sql_query, **dataframes_dict):
    logger.info(f"Performing transformation...\n {' ' * 34} {sql_query}")
    pysql = lambda q: sqldf(q, dataframes_dict)    
    return pysql(sql_query)
    
def df_count(sql_query, **dataframes_dict):    
    pysql = lambda q: sqldf(q, dataframes_dict)
    count= pysql(sql_query)
    return count['count'].iloc[0]        
    
def delete_old_folders(directory, days_to_keep):
    logger.info(f"Deleting folders from {directory} , days_to_keep is {days_to_keep}")
    """
    Delete folders in the specified directory that are older than the specified number of days.

    Parameters:
    - directory (str): The directory path where folders should be deleted.
    - days_to_keep (int): The number of days to keep folders. Folders older than this will be deleted.
    """
    try:
        # Ensure the specified directory is inside the current working directory
        if not os.path.isabs(directory):
            directory = os.path.join(os.getcwd(), directory)

        if not directory.startswith(os.getcwd()):
            raise ValueError("The specified directory must be inside the current working directory.")

        # Calculate the date threshold for deletion
        threshold_date = datetime.datetime.now() - timedelta(days=days_to_keep)

        # List folders in the directory
        folders_to_delete = [
            folder
            for folder in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, folder))
            and parse_date_from_foldername(folder) is not None
            and parse_date_from_foldername(folder) < threshold_date.date()
        ] 

        if not folders_to_delete:
            logger.warning(f"No folders to delete older then  last {days_to_keep} days.\n {' ' * 34}")
        else:
            # Delete folders
            for folder_name in folders_to_delete:
                folder_path = os.path.join(directory, folder_name)
                shutil.rmtree(folder_path)
                logger.info(f"Deleted folder: {folder_path}")

            logger.info(f"Deletion process is finished. Folders that are older than {days_to_keep} days have been successfully removed\n {' ' * 34}")           
           
    except Exception as e:
        logger.error(f"Error deleting folders: {e}")

def parse_date_from_foldername(folder_name):    
    """
    Parse the date from a folder name with the format "YYYYMMDD".

    Parameters:
    - folder_name (str): The folder name.

    Returns:
    - date: The parsed date.
    """
    try:
        return datetime.datetime.strptime(folder_name, "%Y%m%d").date()
    except ValueError:
        return None

# Example usage:
# delete_old_folders("your_directory", 7)  # Delete folders older than 7 days

def get_date_range(delta_days):
        date_from= (datetime.datetime.now() - timedelta(days=delta_days)).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S.000')
        date_to = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.000')
        
        logger.info('Configuring delta parameters..... \n   Date_from              |    Date_to   \n' +
            f'{date_from}   |   {date_to}\n')
        return (date_from, date_to)

def count_dataframe_records(data_frame):    
    record_count = data_frame.shape[0]  
    return record_count
    
def union_dataframes(*args):    
    union_result = pd.concat(args, axis=0, ignore_index=True)
    return union_result

def setup_directories(directories): 
    logger.info("Managing files and folders...")
    # Create directories if they don't exist
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Folder created: {dir_path}")
        else:
            #logger.info(f"Folder already exists: {dir_path}")
            pass
    return directories









def get_conn_engin(database_key, credential):
    credentials_filename = "main/credentials.json"
    connector = db_connector(credentials_filename)
    db_config = connector.load_credentials_from_json(credential)

    if database_key.upper() == 'MYSQL':
        connection = connector.mysql(database_key)
        engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}")
        logger.info(f"Connection established with {database_key} database")
    elif database_key.upper() == 'POSTGRES':
        connection = connector.postgres(database_key)
        engine = create_engine(f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}")
        logger.info(f"Connection established with {database_key} database")
    elif database_key.upper() == 'SNOWFLAKE':
        connection = connector.snowflake(database_key)
        engine = create_engine(
            f"snowflake://{db_config['user']}:{db_config['password']}@{db_config['account']}/{db_config['database']}?warehouse={db_config['warehouse']}&schema={db_config['schema']}&role={db_config.get('role', 'ACCOUNTADMIN')}",
            echo=True
        )
        logger.info(f"Connection established with {database_key} database")
    elif database_key.upper() == 'MSSQL':
        connection = connector.mssql(database_key)       
        connection_string = f'DRIVER={{SQL Server}};SERVER={db_config["server"]};DATABASE={db_config["database"]};Trusted_Connection=yes;'
        engine = create_engine(f'mssql+pyodbc:///?odbc_connect={connection_string}')
        logger.info(f"Connection established with {database_key} database")
    else:
        logger.error(f"Unsupported database key: {database_key}")
        return None
    return([connection,engine])


def read_file(script_name,file_name):  
    logger.info(f'Reading file : source_file/{script_name}/{file_name}')         
    file_path = os.path.join('source_file', script_name, file_name)  
    try:                  
        df = pd.read_csv(file_path)
    except pd.errors.ParserError:  # Catching specific error for parsing CSV
        try:
            df = pd.read_excel(file_path)
        except (pd.errors.ExcelFileError, ValueError):  # Catching specific errors for Excel
            logger.info(f'Unsupported file format for file: {file_path}')
            return None
    except Exception as e:
        logger.info(f'An unexpected error occurred: {e}')
        return None
    return df