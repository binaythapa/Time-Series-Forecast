import concurrent.futures
from main.common import *
from main.stage import *
from SQL.mysql_sql import *
from SQL.DDL.config_ddl import *
  
    
def main():  
          
    postgre = get_conn_engin(database_key = 'POSTGRES', credential = 'POSTGRES')     
    source_engine= postgre[1]
    source_extraction_query= postgres_query 
        
    mysql = get_conn_engin(database_key = 'MYSQL', credential = 'MYSQL') 
    dest_conn = mysql[0]
    dest_engine = mysql[1]    
      
    
    transfer_data_from_source_to_dest(source_engine, source_extraction_query, dest_engine, dest_conn, table_name=script_name,schema='mystyle',chunk_size=1)
      
    #source_connection = connector.mysql('MYSQL')    
    #transfer_data_from_source_to_csv(source_connection, mysql_query, script_name,chunk_size=500000)


    #postgre = get_conn_engin(database_key = 'POSTGRES', credential = 'POSTGRES')
    #target_database_engine = postgre[1]
    #transfer_data_from_csv_to_target_database(target_database_engine, script_name,table_name=script_name)
     
if __name__ == "__main__":
    script_name= 'etl'    
    basic_setup(script_name)
    credentials_filename = "main/credentials.json"
    connector = db_connector(credentials_filename)    
     
    main()   
