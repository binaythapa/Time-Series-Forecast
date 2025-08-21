
#Pipeline
import concurrent.futures
from main.common import *
from main.stage_mysql import *
from SQL.DDL.config_ddl import *

    
def get_parameter(script_name):
    connector= basic_setup(script_name)    

    # Multithreading Implimentation
    with concurrent.futures.ThreadPoolExecutor() as executor:

        try:
            future_mysql = executor.submit(connector.mysql,'MYSQL',get_date,[script_name]) 
            df_mysql= future_mysql.result()  
        
            start_date = df_mysql['end_datetime'].iloc[0].strftime('%Y-%m-%d %H:%M:%S.000')
            end_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.000')
        except:
            start_date= (datetime.datetime.now() - timedelta(days=100)).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S.000')
            end_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.000')
        df = [start_date, end_date]
        return df       
           
    logger.info(f"{script_name}.py Run Successfully.................")  
    

     
        
    
