import pandas as pd
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from main.log import *
#from main.connector import *
from main.common import *

def upload_data_to_database(connection, engine, dataframes_dict, script_name, schema, append=False):
    chunk_size = 500000  # Adjust chunk size as needed    

    # Create a sessionmaker for the engine
    Session = sessionmaker(bind=engine)
    
    try:
        session = Session()
        for df_name, df in dataframes_dict.items():
            table_name = f"{script_name}_{df_name}"
            
            if not append:                
                try:
                   
                    sql_statement = text(f"TRUNCATE TABLE {schema}.{table_name}")                   
                    session.execute(sql_statement)
                    logger.info(f"Table {table_name} truncated successfully")
                except Exception as e:
                    logger.error(f"Unable to truncate {schema}.{table_name}: {e}")
            
            logger.info(f"Appending data into {table_name}...")

            # Write DataFrame to database table in chunks
            for i in range(0, len(df), chunk_size):
                df_chunk = df[i:i+chunk_size]
                df_chunk.to_sql(name=table_name, con=engine, if_exists='append', index=False)
                logger.info(f"{df_chunk.shape[0]} records appended")

            logger.info(f"Total {df.shape[0]} records inserted into {table_name}\n")        
        session.commit()

    except Exception as e:
        logger.error("Error uploading data to database:", e)        
        session.rollback()

    finally:        
        session.close()       
        connection.close()




def transfer_data_from_source_to_dest(source_engine, source_extraction_query, dest_engine, dest_conn, table_name, schema, chunk_size=50000):
    Session = sessionmaker(bind=dest_engine)
    
    try:
        session = Session()
        
        # Truncate destination table within a transaction
        with session.begin():
            try:
                full_table_name = f"{schema}.{table_name}"
                sql_statement = text(f"TRUNCATE TABLE {full_table_name}")                   
                session.execute(sql_statement)
                logger.info(f"{full_table_name} truncated successfully")
            except: 
                pass

            i = 0
            # Load data into destination in chunks
            logger.info(source_extraction_query)
            for chunk in pd.read_sql_query(source_extraction_query, source_engine, chunksize=chunk_size):
                chunk.to_sql(table_name, dest_engine, schema=schema, if_exists='append', index=False)
                logger.info(f"{chunk.shape[0]} records transferred successfully in {schema}.{table_name}")
                i += chunk.shape[0]

            logger.info(f"{i} records transferred successfully.")    
        session.commit()

    except Exception as e:     
        session.rollback()
        logger.info("Error during data transfer:", e)

    finally:        
        session.close()


def transfer_data_from_source_to_csv(source_connection, query,script_name,chunk_size=50000):    
    dir = get_outbound_directory(script_name)
    setup_directories(dir)

    try:
        i = 0
        # Load data into CSV files in chunks
        for chunk in pd.read_sql(query, source_connection, chunksize=chunk_size):
            # Save chunk to CSV file
            csv_filename = f"{script_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            csv_path = os.path.join(dir[2], csv_filename)
            chunk.to_csv(csv_path, index=False)
            logger.info(f"{chunk.shape[0]} rows saved to {csv_filename}")
            i += chunk.shape[0]
        logger.info(f"{i} record extracted successfully.")
    except Exception as e:
        logger.info("Error during data transfer:", e)
    finally:
        # Close MySQL connection
        if source_connection:
            source_connection.close()
        pass

def transfer_data_from_csv_to_target_database(target_database_engine, script_name,schema,table_name):
    # Assuming get_outbound_directory and move_files functions are defined elsewhere
    extraction_directory = get_outbound_directory(script_name)[2]
    date_folder = get_outbound_directory(script_name)[4]
    
    # Create SQLAlchemy session maker
    Session = sessionmaker(bind=target_database_engine)
    
    try:
        total_records = 0
        
        # Open session
        with Session() as session:
            # Truncate destination table within a transaction
            with session.begin():
                try:
                    sql_statement = text(f"TRUNCATE TABLE {table_name}")                   
                    session.execute(sql_statement)
                    logger.info(f"Table {table_name} truncated successfully")
                except Exception as truncate_error:
                    logger.info(f"Unable to truncate table {table_name}: {truncate_error}")

        # Iterate through CSV files in the extraction directory
        for filename in os.listdir(extraction_directory):
            if filename.endswith(".csv"):
                csv_path = os.path.join(extraction_directory, filename)

                # Load CSV file into DataFrame
                chunk = pd.read_csv(csv_path)

                # Open session
                with Session() as session:
                    # Begin transaction to append data
                    with session.begin():
                        # Load data into target database
                        chunk.to_sql(table_name, target_database_engine, if_exists='append', index=False)

                # Print status
                logger.info(f"{filename}: {chunk.shape[0]} records transferred to table {table_name} .")
                
                # Move processed files
                move_files(extraction_directory, date_folder, starts_with=filename)
                
                # Update total records transferred
                total_records += chunk.shape[0]
        
        logger.info(f"Total {total_records} records transferred successfully.")
    
    except Exception as e:
        logger.info("Error during data transfer:", e)






