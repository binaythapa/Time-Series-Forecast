
#Pipeline

import concurrent.futures
from main.common import *
from main.stage_mysql import *
from SQL.DDL.config_ddl import *

    
def main():
    
    # Multithreading Implimentation
    with concurrent.futures.ThreadPoolExecutor() as executor:  
        #values = ("aaa", "2025-03-31 11:00:00", "2025-03-31 12:00:00", "2025-03-31", "success")
        future_mysql = executor.submit(connector.mysql,'MYSQL',ddl) 
        df_mysql= future_mysql.result()  
        print(df_mysql)   
    
    logger.info(f"{script_name}.py Run Successfully.................")  
    
if __name__ == "__main__":
    script_name= 'config'   
    connector= basic_setup(script_name)     
    main()   
