from main.connector import *
from main.time_series import *
#import mysql.connector



def basic_setup(script_name):
    show_logo(script_name)
    log(script_name)
    handler = DatabaseHandler()        
    return handler 

def file_folders_manage(script_name):
    current_date = datetime.datetime.now()   
    current_directory = os.getcwd()   
   # Specify subdirectories based on the provided script_name
    current_directory = os.getcwd()
    index_directory = os.path.join(current_directory, 'index')
    script_directory = os.path.join(index_directory, script_name)
    archive_directory = os.path.join(script_directory, 'archive')
    ready_to_load_directory = os.path.join(script_directory, 'ReadyToLoad')
    analysis_directory = os.path.join(script_directory, 'analysis')
    date_folder = os.path.join(archive_directory, current_date.strftime("%Y%m%d"))

    # Create a list of directory paths
    dir = [script_directory, archive_directory, date_folder, ready_to_load_directory, analysis_directory]
    setup_directories(dir)
    
    #Move Index to archive
    move_files(ready_to_load_directory,date_folder,starts_with=script_name)    
      
    #Delete old index_archieve folders
    delete_old_folders(archive_directory, 7)
    
    return dir
    
class DatabaseHandler:
    def __init__(self):
        self.credentials_filename = "main/credentials.json"
        self.conn = db_connector(self.credentials_filename)
        
    def snowflake(self, database_key, sql_query, date_parameters=None):
        return self.conn.execute_query_and_fetch_data(self.conn.snowflake(database_key), sql_query, date_parameters)
    
    def mssql(self, database_key, sql_query, date_parameters=None):
        return self.conn.execute_query_and_fetch_data(self.conn.mssql(database_key), sql_query, date_parameters)
    
    def mysql(self, database_key, sql_query, date_parameters=None):
        return self.conn.execute_query_and_fetch_data(self.conn.mysql(database_key), sql_query, date_parameters)

    def postgres(self, database_key, sql_query, date_parameters=None):
        return self.conn.execute_query_and_fetch_data(self.conn.postgres(database_key), sql_query, date_parameters)

    def oracle(self, database_key, sql_query, date_parameters=None):
        return self.conn.execute_query_and_fetch_data(self.conn.oracle(database_key), sql_query, date_parameters)
    

def get_outbound_directory(script_name):
    current_date = datetime.datetime.now()   
    current_directory = os.getcwd()    
    index_directory = os.path.join(current_directory, 'outbound')
    script_directory = os.path.join(index_directory, script_name)
    extraction_directory = os.path.join(script_directory, 'extraction')
    archive_directory = os.path.join(script_directory, 'archive')    
    date_folder = os.path.join(archive_directory, current_date.strftime("%Y%m%d"))

    # Create a list of directory paths
    dir = [index_directory,script_directory, extraction_directory,archive_directory, date_folder]
    return dir