
from main.connector import *

current_date = datetime.datetime.now().strftime("%Y%m%d") 
credentials_filename = "main/credentials.json"
connector = db_connector(credentials_filename) 
script_name = 'etl_job_2'

mysql = get_conn_engin(database_key = 'MYSQL', credential = 'MYSQL') 
connection = mysql[0]
engine = mysql[1] 


query = '''
select * from etl_config where etl_date = %s and job_name = %s;
'''
'''
parameter = [current_date,script_name]

df = connector.execute_query_and_fetch_data(connection, query,parameter) 


#print(df)
# Convert dictionary to DataFrame
#df = pd.DataFrame(df)

date_from= df["from"]
date_to= df["to"]  
# Convert 'from' and 'to' columns to list of strings
#from_dates = df['from'].tolist()
#to_dates = df['to'].tolist()
date = [date_from,date_to]

# Combine into a single list
#date_list = [str(from_dates) ,str(to_dates)]

print(date)
'''