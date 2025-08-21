
#Pipeline

import concurrent.futures
from scripts.finale.test import *
#from scripts.finale.get_parameter import *
from main.common import *
from main.stage_mysql import *
from SQL.etl_sql import *


    
def main():
    
    
    # Multithreading Implimentation
    with concurrent.futures.ThreadPoolExecutor() as executor:                       
        future_excel = executor.submit(read_file,script_name,file_name='etl.csv')
       # future_postgres = executor.submit(connector.postgres,'POSTGRES',postgres_query,date_parameter)  

        df_excel= future_excel.result() 
        #df_excel = future_postgres.result()        
       
    
    #Transformation
    #df_union = run_sql(transform_script, df_postgres=df_postgres, df_excel=df_excel)     

    
    #Loading
    dataframes_dict = {'sales' : df_excel}       
    upload_data_to_mysql(dataframes_dict, script_name, append=False)
    
    
    #Log Management
    insert_or_update_logs(script_name,date_parameter,load_type)
    logger.info(f"{script_name}.py Run Successfully.................")  
    
    
if __name__ == "__main__":
    script_name= 'etl'   
    connector= basic_setup(script_name)  
    date_parameters = execute_select_query(script_name)
    date_parameter= (date_parameters[0],date_parameters[1])
    load_type = (date_parameters[2])   
    main()   
   
