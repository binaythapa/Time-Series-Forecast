
#Pipeline

import concurrent.futures
from scripts.finale.test import *
#from scripts.finale.get_parameter import *
from main.common import *
from main.stage_mysql import *
from main.stage_postgre import *
from SQL.etl_sql import *


    
def main():
    
    
    # Multithreading Implimentation
    with concurrent.futures.ThreadPoolExecutor() as executor:       
                     
        future_excel = executor.submit(read_file,script_name,file_name='Backorder_demo.csv')         
        df_excel= future_excel.result()  
        print(df_excel)      

    #Loading to staging
    dataframes_dict = {'sales' : df_excel}       
    #upload_data_to_mysql(dataframes_dict, script_name, append=False)  
    upload_data_to_postgresql(dataframes_dict, script_name)
 
    #insert_or_update_logs(script_name,date_parameter,load_type)
    logger.info(f"{script_name}.py Run Successfully.................")  
    
if __name__ == "__main__":
    script_name= 'qlik'   
    connector= basic_setup(script_name)  
    
    main()   
   
