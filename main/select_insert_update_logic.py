

##select_insert_update_logic.py

from main.log import *
from main.connector import *
from SQL.DDL.config_ddl import *  # Assuming this is your INSERT query
import datetime
from datetime import timedelta
import pandas as pd



# Create an instance of DBConnector
credentials_filename = "main/credentials.json"
connector = db_connector(credentials_filename)

# Establish connection to the database
connection = connector.mysql('MYSQL')
cursor = connection.cursor()
logger.info("Connected to the database successfully.") 

def execute_insert_query(insert_query, *args):  
   
    try:
        insert_values =  args    #(script_name, start_datetime, end_datetime, rundate, status, load_type)        
        cursor.execute(insert_query, insert_values)
        connection.commit()  # Commit the transaction        
        logger.info(f"Data inserted successfully:{insert_query} \n -: {insert_values} \n\n")

    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        connection.rollback()  # Rollback in case of error

def execute_update_query(update_query,*args):
    
    try:
        update_values = args
        cursor.execute(update_query, update_values)
        connection.commit();  
        logger.info(f"Data updated successfully : {update_query} \n -: {update_values}\n\n")
       

    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        connection.rollback()  # Rollback in case of error
        logger.info("rollback")


def execute_select_query(script_name):
    try:
        # Execute the select query to fetch data
        cursor.execute(select_query, (script_name,))          
        
        try:
            query_results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            query_results = [list(row) for row in query_results]
            df = pd.DataFrame(query_results, columns=columns)            
        
            # Assuming 'end_datetime' is a column in the fetched data
            start_date = df['end_datetime'].iloc[0].strftime('%Y-%m-%d %H:%M:%S.000')
            end_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.000')
            load_type = 'incremental'
           
            
           
        except:                       
            start_date= (datetime.datetime.now() - timedelta(days=6000)).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S.000')
            end_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.000')
            load_type = 'full'
           
        df = [start_date, end_date,load_type]
        return df   


    except mysql.connector.Error as err:
        logger.error(f"Error fetching data: {err}")


def insert_or_update_logs(script_name, date_parameter,load_type):
    start_datetime=date_parameter[0]
    end_datetime =date_parameter[1]
    rundate = date_parameter[1] 
    status = 'Completed'

    table_name = 'logs_history'
    insert_query =  f'''
    INSERT INTO {table_name} (script_name, start_datetime, end_datetime, rundate, status, load_type)
    VALUES (%s, %s, %s, %s, %s, %s)
    '''
    execute_insert_query(insert_query,script_name, start_datetime, end_datetime, rundate, status, load_type)


    if load_type == 'full':
        table_name = 'logs'
        insert_query =  f'''
    INSERT INTO {table_name} (script_name, start_datetime, end_datetime, rundate, status, load_type)
    VALUES (%s, %s, %s, %s, %s, %s)'''        
        execute_insert_query(insert_query,script_name, start_datetime, end_datetime, rundate, status, load_type)

    else:
        table_name = 'logs'
        update_query = f"""
        UPDATE {table_name}
        SET status = %s, start_datetime = %s, end_datetime = %s,rundate = %s,load_type = %s
        WHERE script_name = %s
        """
        execute_update_query(update_query,status,start_datetime, end_datetime, rundate, load_type,script_name)


'''
if __name__ == "__main__":
    execute_insert_query()  # Insert the data
    execute_update_query()  # Update the data
    execute_select_query()  # Fetch and log the data

    # Ensure the cursor and connection are closed
if cursor:
    cursor.close()
    logger.info("Cursor closed.")
if connection:
    connection.close()
    logger.info("Connection closed.")
'''