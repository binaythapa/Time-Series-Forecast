import concurrent.futures
from main.common import *
from main.stage import *
from ETL.SQL.etl_sql import *
from SQL.DDL.config_ddl import *
  
    
def main():   
      
    source_connection = connector.mysql('MYSQL')    
    transfer_data_from_source_to_csv(source_connection, mysql_query, script_name,chunk_size=5000)
    postgre = get_conn_engin(database_key = 'POSTGRES', credential = 'POSTGRES')
    target_database_engine = postgre[1]
    transfer_data_from_csv_to_target_database(target_database_engine, script_name,schema='public',table_name=script_name)

    logger.info(f"{script_name}.py Run Successfully.................") 
     
if __name__ == "__main__":
    script_name= 'etl'
    basic_setup(script_name)    
    credentials_filename = "main/credentials.json"
    connector = db_connector(credentials_filename)    
     
    main()   
