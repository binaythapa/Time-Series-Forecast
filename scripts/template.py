
#Pipeline

import concurrent.futures
from scripts.finale.test import *
from main.common import *
from main.stage_mysql import *
from SQL.etl_sql import *


    
def main():
    
    
    # Multithreading Implimentation
    with concurrent.futures.ThreadPoolExecutor() as executor:       
        #future_snow = executor.submit(connector.snowflake,'snowflake',snow_query) 
        #future_mssql = executor.submit(connector.mssql,'MSSQL',mssql_query) 
        #future_postgres = executor.submit(connector.postgres,'POSTGRES',postgres_query,date_parameter)               
        future_excel = executor.submit(read_file,script_name,file_name='etl.csv') 


        #df_snow = future_snow.result()
        #df_mssql = future_mssql.result()  
        #df_postgres = future_postgres.result()
        df_excel= future_excel.result()  
       
    
    #Transformation
    #df_union = run_sql(transform_script, df_postgres=df_postgres, df_excel=df_excel)     

    #Loading to staging
    dataframes_dict = {'sales' : df_excel}       
    upload_data_to_mysql(dataframes_dict, script_name, append=True)
    
    
    #dir = file_folders_manage(script_name)  

    # Analysis path
    #analysis_path = os.path.join(dir[4], f'{script_name}_analysis.xlsx')
    #write_to_excel([df_postgres,df_excel,df_union],file_name=analysis_path, sheet_name=['postgres','excel','union'])
    
    #execute_update_query(status,script_name,date_parameter,load_type)
    #insert_or_update_logs(script_name,date_parameter,load_type)
    logger.info(f"{script_name}.py Run Successfully.................")  
    
if __name__ == "__main__":
    script_name= 'etl'   
    connector= basic_setup(script_name)  
    #date_parameters = execute_select_query(script_name)
    #date_parameter= (date_parameters[0],date_parameters[1])
    #load_type = (date_parameters[2])   
    main()   
   
