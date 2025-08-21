import concurrent.futures
from scripts.finale.test import *
from main.common import *
from main.stage_mysql import *
from SQL.etl_sql import *
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import warnings
warnings.filterwarnings("ignore")
from main.log import *

def detect_and_reshape(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect required columns, identify date columns dynamically,
    and reshape from wide to long format.

    Returns:
        pd.DataFrame: Reshaped DataFrame with columns ['Material', 'Date', 'Sales'].
    Raises:
        ValueError: If required columns or date columns are missing.
    """
    # Detect required columns
    required_columns = ['Material']
    if not all(col in df.columns for col in required_columns):
        missing = list(set(required_columns) - set(df.columns))
        raise ValueError(f"Missing required columns: {missing}")

    # Identify date columns dynamically (after 'Material')
    date_columns = df.columns[9:]
    if len(date_columns) == 0:
        raise ValueError("No date columns found in provided dataframe.")

    # Reshape data
    df_long = df.melt(
        id_vars=['Material'],
        value_vars=date_columns,
        var_name='Date',
        value_name='Sales'
    )

    return df_long



def main():   
   
    # Instead of reading inside the function, read once outside     
    df = pd.read_csv(r"D:\Projects\ETL\ETL\source_file\ml_sales\cosmetics_sales_data.csv")     
    df_long= df
    
    splits = {
        'df_long': df_long,
        'dimension_col': 'Product',#'ITEM CODE',#'Material',
        'date_col': 'Date',
        'value_col': 'Amount ($)',
        'freq': 'D',         # 'MS' for monthly, 'D' for daily, etc.
        'test_size': 12,      # Last 12 periods for testing
        'min_history': 24  ,   # Minimum history to proceed
        'test_mode':True,
        'forecast_periods': 12
    } 
    # Now you have:
    # df_long  -> Cleaned and reshaped data
    # materials -> List of unique materials
    # error_df  -> Rows with missing or problematic data for later analysis
   
    
    df_long, error_df,materials = load_and_prepare_data(df_long, splits)      

    dataframes_dict = {'source' : df_long, 'rejected_data':error_df} 
    upload_data_to_mysql(dataframes_dict, script_name, append=False)   
    
    logger.info("Running Prophet Model ...")
    run_prophet_model(df_long, materials,script_name,False,splits)  

    '''   

    logger.info("Running Holt-Winters Model...")
    run_holt_winters_model(df_long, materials,script_name,splits)    

    
    logger.info("Running SARIMA Model...")
    run_sarima_model(df_long, materials,script_name,splits)

    
    logger.info("Running ARIMA Model...")
    run_arima_model(df_long, materials,script_name,splits)
    
   
    logger.info("Running MLPRegressor Model...")
    run_mlp_model(df_long, materials,script_name,splits)
    
    
    logger.info("Running LSTM Model...")
    run_lstm_model(df_long, materials,script_name,splits)
    
    
    dataframes_dict = {'source' : df_long, 'rejected_data':error_df} 
    upload_data_to_mysql(dataframes_dict, script_name, append=False)     

    '''


if __name__ == "__main__":
    script_name = 'cosmetic'
    connector = basic_setup(script_name)    
    main()
