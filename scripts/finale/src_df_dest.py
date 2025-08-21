import concurrent.futures
from main.common import *
from main.stage import *
from SQL.mysql_sql import *
from SQL.DDL.config_ddl import *
  
    
def main(): 
          
    # Multithreading Implimentation
    with concurrent.futures.ThreadPoolExecutor() as executor:       
        future_snow = executor.submit(connector.snowflake,'snowflake',snowflake_query) 
              
        df_snow = future_snow.result()

    
    dir = file_folders_manage(script_name)    
    
   
    index_path = os.path.join(dir[3],f'{script_name}_{current_datetime}.xlsx')
    write_to_csv(df_snow, file_name=index_path)  

    dataframes_dict = {'test' : df_snow}
        
    mysql = get_conn_engin(database_key = 'MYSQL', credential = 'MYSQL') 
    connection = mysql[0]
    engine = mysql[1]

    #upload_data_to_database(dataframes_dict,connection=dest_conn,engine=dest_engine, script_name,schema='mystyle')
    upload_data_to_database(connection,engine,dataframes_dict, script_name, schema='mystyle',append=False)
    logger.info(f"{script_name}.py Run Successfully.................")  
    '''
    postgre = get_conn_engin(database_key = 'POSTGRES', credential = 'POSTGRES')     
    source_engine= postgre[1]
    source_extraction_query= postgres_query    
    table_name= script_name
    transfer_data_from_source_to_dest(source_engine, source_extraction_query, dest_engine, dest_conn, table_name,schema='mystyle',chunk_size=1)
      
    #source_connection = connector.mysql('MYSQL')    
    #transfer_data_from_source_to_csv(source_connection, mysql_query, script_name,chunk_size=500000)


    #postgre = get_conn_engin(database_key = 'POSTGRES', credential = 'POSTGRES')
    #target_database_engine = postgre[1]
    #transfer_data_from_csv_to_target_database(target_database_engine, script_name,table_name=script_name)
     '''
if __name__ == "__main__":
    script_name= 'test'   
    connector= basic_setup(script_name) 
    credentials_filename = "main/credentials.json"
    #connector = db_connector(credentials_filename)    
    current_date = datetime.datetime.now().strftime("%Y%m%d")  
    current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")    
    main()   
