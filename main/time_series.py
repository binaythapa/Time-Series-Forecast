import concurrent.futures
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

# CLEANING STEP: Replace NaN, inf, -inf with None or suitable placeholder
def clean_dataframe(df, df_name):
    logger.info(f"Cleaning DataFrame '{df_name}' before upload...")
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    before = len(df)

    # Only drop rows if all required columns exist
    required_cols = ['RMSE', 'MAE', 'MAPE (%)']
    existing_cols = [col for col in required_cols if col in df.columns]

    if existing_cols:
        df = df.dropna(subset=existing_cols, how='any')
    else:
        logger.warning(
            f"DataFrame '{df_name}' does not contain expected metric columns {required_cols}. Skipping drop step."
        )

    after = len(df)
    logger.info(f"Cleaned '{df_name}': Dropped {before - after} rows with invalid metric values.")
    return df


def clean_metrics(metrics):
    """
    Replace inf, -inf, and NaN in metrics dictionary with None
    """
    return {
        k: None if (isinstance(v, (float, np.floating)) and not np.isfinite(v)) else v
        for k, v in metrics.items()
    }

def mape(y_true, y_pred):
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def create_supervised(data, window_size):
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i+window_size])
        y.append(data[i+window_size])
    return np.array(X), np.array(y)


def load_and_prepare_data(df: pd.DataFrame, splits: dict):
    try:
        logger.info("Starting data validation and reshaping.")

        df_long = df.copy()

        # Extract column names from config
        dimension_col = splits['dimension_col']
        date_col = splits['date_col']
        value_col = splits['value_col']      

        # Convert dates & detect invalid
        df_long[date_col] = pd.to_datetime(df_long[date_col], errors='coerce')        
      
        # Add validation flags
        df_long['Error_Flag'] = ""
        df_long.loc[df_long[dimension_col].isna(), 'Error_Flag'] += f"Missing {dimension_col}; "
        df_long.loc[df_long[date_col].isna(), 'Error_Flag'] += f"Invalid {date_col}; "
        df_long.loc[df_long[value_col].isna(), 'Error_Flag'] += f"Missing {value_col}; "
        df_long.loc[~pd.to_numeric(df_long[value_col], errors='coerce').notna(), 'Error_Flag'] += f"Non-numeric {value_col}; "

        # Separate clean and error data
        df_errors = df_long[df_long['Error_Flag'] != ""].copy()
        df_long_clean = df_long[df_long['Error_Flag'] == ""].copy()

        # Remove helper column from clean data
        df_long_clean.drop(columns=['Error_Flag'], inplace=True)

        # Unique materials from clean data
        materials = df_long_clean[dimension_col].unique()

        logger.info(f"Data reshaping complete. Clean rows: {len(df_long_clean)}, Errors: {len(df_errors)}")

        return df_long_clean, df_errors, materials

    except Exception as e:
        logger.error(f"Error during data processing: {e}", exc_info=True)
        raise


def finalize_and_upload(df_long, all_forecasts, all_metrics, script_name, append=True,
                        all_train_records=None, all_test_records=None):
    try:
        # Combine forecast and metrics
        forecast_combined = pd.concat(all_forecasts, ignore_index=True)
        metrics_combined = pd.DataFrame(all_metrics)

        # Clean metrics
        metrics_combined = clean_dataframe(metrics_combined, 'metrics_combined')
        logger.info("Forecasts and metrics combined and cleaned successfully.")

        # Prepare data dictionary for upload
        dataframes_dict = {
            'forecast': forecast_combined,
            'forecast_error': metrics_combined
        }

        # Include train records if provided
        if all_train_records:
            train_combined = pd.concat(all_train_records, ignore_index=True)
            dataframes_dict['train'] = train_combined

        # Include test records if provided
        if all_test_records:
            test_combined = pd.concat(all_test_records, ignore_index=True)
            dataframes_dict['test'] = test_combined

        # Upload to MySQL
        upload_data_to_mysql(dataframes_dict, script_name, append)

    except Exception as e:
        logger.error(f"Error during final upload or logging: {e}", exc_info=True)
        raise

def prepare_train_test_split(df_long, material, splits):

    """
            Prepares train and test sets for a specific material using configurable options.
    """

    # Unpack config values from splits
    dimension_col = splits['dimension_col']
    date_col = splits['date_col']
    value_col = splits['value_col']
    freq = splits['freq']    
    min_history = splits['min_history']
    test_mode = splits['test_mode']
    test_size = splits['test_size']

    # Filter and prepare time series
    ts = df_long[df_long[dimension_col] == material][[date_col, value_col]].sort_values(date_col)
    ts = ts.set_index(date_col).resample(freq).sum()

    # Skip if insufficient history
    if len(ts) < min_history:
        return None, None, None

    if test_mode:
        # Split into train/test
        train = ts[:-test_size]
        test = ts[-test_size:]
    else:
        # Full data for training, no test set needed
        train = ts
        test = None

    return train, test, ts


def run_prophet_model(df_long, materials, script_name, append, splits):
    """
    Runs Prophet forecasting for each material with optional test_mode.
    """

    value_col = splits['value_col']
    date_col = splits['date_col']
    dimension_col = splits['dimension_col']
    freq = splits['freq']    
    test_size = splits['test_size']
    test_mode = splits['test_mode']
    forecast_periods= splits['forecast_periods']
    
    all_forecasts = []
    all_metrics = []
    all_train_records = []
    all_test_records = []

    for material in materials:
        train, test, ts = prepare_train_test_split(df_long, material, splits)
        if train is None:
            continue

        try:
            logger.info(f"PROPHET started for {material}")
            prophet_train = train.reset_index().rename(columns={date_col: "ds", value_col: "y"})
            model = Prophet()
            model.fit(prophet_train)

            # Forecast horizon depends on mode
            forecast_periods = test_size if test_mode else splits.get('forecast_period', 12)
            future = model.make_future_dataframe(periods=forecast_periods, freq=freq)
            forecast = model.predict(future)

            if test_mode and test is not None:
                # Test set forecast
                forecast_test = forecast[['ds', 'yhat']].set_index('ds').loc[test.index]

                # Calculate metrics
                prophet_rmse = np.sqrt(mean_squared_error(test[value_col], forecast_test['yhat']))
                prophet_mae = mean_absolute_error(test[value_col], forecast_test['yhat'])
                prophet_mape = mape(test[value_col].values.flatten(), forecast_test['yhat'].values)

                all_metrics.append({
                    'Model': 'Prophet',
                    dimension_col: material,
                    'RMSE': prophet_rmse,
                    'MAE': prophet_mae,
                    'MAPE (%)': prophet_mape
                })

                # Store test data
                test_df = test.copy().reset_index()
                test_df[dimension_col] = material
                test_df['Model'] = 'Prophet'
                all_test_records.append(test_df)

            # Store forecast
            prophet_future = forecast[['ds', 'yhat']].tail(forecast_periods).copy()
            prophet_future.columns = [date_col, value_col]
            prophet_future[dimension_col] = material
            prophet_future['Model'] = 'Prophet'
            all_forecasts.append(prophet_future)

            # Store train data only in test mode
            if test_mode:
                train_df = train.copy().reset_index()
                train_df[dimension_col] = material
                train_df['Model'] = 'Prophet'
                all_train_records.append(train_df)

        except Exception as e:
            logger.error(f"Prophet failed for {material}: {e}", exc_info=True)

    # Finalize and upload
    finalize_and_upload(
        df_long,
        all_forecasts,
        all_metrics if test_mode else [],  # Only store metrics in test mode
        script_name,
        append,
        all_train_records=all_train_records if test_mode else None,
        all_test_records=all_test_records if test_mode else None
    )



def run_holt_winters_model(df_long, materials, script_name, splits):
    value_col = splits['value_col']
    date_col = splits['date_col']
    dimension_col = splits['dimension_col']
    freq = splits.get('freq', 'MS')
    test_size = splits.get('test_size', 12)
    test_mode = splits['test_mode']
    periods_to_forecast= splits['forecast_periods']

    all_forecasts = []
    all_metrics = []
    all_train_records = []
    all_test_records = []  # Only used in test_mode=True

    for material in materials:
        '''
        if test_mode:
            train, test, ts = prepare_train_test_split(df_long, material, splits)
        else:
            ts = df_long[df_long[dimension_col] == material][[date_col, value_col]].sort_values(date_col)
            ts.set_index(date_col, inplace=True)
            ts = ts.resample(freq).sum()
            if len(ts) < 12:
                logger.warning(f"Not enough data for {material}")
                continue
            train = ts
            test = None

        if train is None:
            continue
        '''
        train, test, ts = prepare_train_test_split(df_long, material, splits)

        try:
            logger.info(f"HOLT-WINTERS started for {material} | test_mode={test_mode}")

            model = ExponentialSmoothing(
                train[value_col], seasonal='add', trend='add', seasonal_periods=12
            ).fit()

            if test_mode:
                forecast = model.forecast(test_size)

                print("Forecast start date:", forecast.index.min())
                print("Forecast end date:", forecast.index.max())


                rmse = np.sqrt(mean_squared_error(test[value_col], forecast))
                mae = mean_absolute_error(test[value_col], forecast)
                mape_val = mape(test[value_col].values.flatten(), forecast.values)

                all_metrics.append({
                    'Model': 'Holt-Winters',
                    dimension_col: material,
                    'RMSE': rmse,
                    'MAE': mae,
                    'MAPE (%)': mape_val
                })

                forecast_dates = pd.date_range(
                    start=train.index[-1] + pd.tseries.frequencies.to_offset(freq),
                    periods=test_size,
                    freq=freq
                )
                hw_future = pd.DataFrame({
                    date_col: forecast_dates,
                    value_col: forecast.values,
                    dimension_col: material,
                    'Model': 'Holt-Winters'
                })
                all_forecasts.append(hw_future)

                train_df = train.copy().reset_index()
                train_df[dimension_col] = material
                train_df['Model'] = 'Holt-Winters'
                all_train_records.append(train_df)

                test_df = test.copy().reset_index()
                test_df[dimension_col] = material
                test_df['Model'] = 'Holt-Winters'
                all_test_records.append(test_df)

            else:
                forecast = model.forecast(periods_to_forecast)
                forecast_dates = pd.date_range(
                    start=ts.index[-1] + pd.tseries.frequencies.to_offset(freq),
                    periods=periods_to_forecast,
                    freq=freq
                )
                hw_future = pd.DataFrame({
                    date_col: forecast_dates,
                    value_col: forecast.values,
                    dimension_col: material,
                    'Model': 'Holt-Winters'
                })
                all_forecasts.append(hw_future)

                train_df = train.copy().reset_index()
                train_df[dimension_col] = material
                train_df['Model'] = 'Holt-Winters'
                all_train_records.append(train_df)

        except Exception as e:
            logger.error(f"Holt-Winters failed for {material}: {e}", exc_info=True)

    # Upload
    if test_mode:
        finalize_and_upload(
            df_long,
            all_forecasts,
            all_metrics,
            script_name,
            append=True,
            all_train_records=all_train_records,
            all_test_records=all_test_records
        )
    else:
        finalize_and_upload(
            df_long,
            all_forecasts,
            all_metrics,  # Will be empty in non-test mode
            script_name,
            append=True,
            all_train_records=all_train_records
        )




def run_sarima_model(df_long, materials, script_name, splits):
    value_col = splits['value_col']
    date_col = splits['date_col']
    dimension_col = splits['dimension_col']
    freq = splits.get('freq', 'MS')
    test_size = splits.get('test_size', 12)
    test_mode = splits['test_mode']
    periods_to_forecast= splits['forecast_periods']

    all_forecasts, all_metrics, all_train_records, all_test_records = [], [], [], []

    for material in materials:

        '''
        if test_mode:
            train, test, ts = prepare_train_test_split(df_long, material, splits)
            if train is None or test is None:
                continue
        else:
            ts = df_long[df_long[dimension_col] == material][[date_col, value_col]].sort_values(date_col)
            ts = ts.set_index(date_col).resample(freq).sum()
            train, test = ts, None

        '''
        train, test, ts = prepare_train_test_split(df_long, material, splits)

        try:
            logger.info(f"SARIMA started for {material}")

            model = SARIMAX(
                train[value_col],
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False
            ).fit(disp=False)

            steps = test_size if test_mode else periods_to_forecast
            forecast = model.forecast(steps=steps)

            # Metrics only in test mode
            if test_mode:
                rmse = np.sqrt(mean_squared_error(test[value_col], forecast))
                mae = mean_absolute_error(test[value_col], forecast)
                mape_val = mape(test[value_col].values.flatten(), forecast.values)
                all_metrics.append({'Model': 'SARIMA', dimension_col: material, 'RMSE': rmse, 'MAE': mae, 'MAPE (%)': mape_val})

            forecast_dates = pd.date_range(start=train.index[-1] + pd.tseries.frequencies.to_offset(freq), periods=steps, freq=freq)
            future_df = pd.DataFrame({date_col: forecast_dates, value_col: forecast.values, dimension_col: material, 'Model': 'SARIMA'})
            all_forecasts.append(future_df)

            train_df = train.copy().reset_index()
            train_df[dimension_col] = material
            train_df['Model'] = 'SARIMA'
            all_train_records.append(train_df)

            if test_mode:
                test_df = test.copy().reset_index()
                test_df[dimension_col] = material
                test_df['Model'] = 'SARIMA'
                all_test_records.append(test_df)

        except Exception as e:
            logger.error(f"SARIMA failed for {material}: {e}", exc_info=True)

    finalize_and_upload(
        df_long, all_forecasts, all_metrics if test_mode else [],
        script_name, append=True,
        all_train_records=all_train_records,
        all_test_records=all_test_records if test_mode else []
    )


def run_arima_model(df_long, materials, script_name, splits):
    value_col = splits['value_col']
    date_col = splits['date_col']
    dimension_col = splits['dimension_col']
    freq = splits.get('freq', 'MS')
    test_size = splits.get('test_size', 12)
    test_mode = splits['test_mode']
    periods_to_forecast= splits['forecast_periods']

    all_forecasts, all_metrics, all_train_records, all_test_records = [], [], [], []

    for material in materials:

        '''
        if test_mode:
            train, test, ts = prepare_train_test_split(df_long, material, splits)
            if train is None or test is None:
                continue
        else:
            ts = df_long[df_long[dimension_col] == material][[date_col, value_col]].sort_values(date_col)
            ts = ts.set_index(date_col).resample(freq).sum()
            train, test = ts, None
        '''
        train, test, ts = prepare_train_test_split(df_long, material, splits)
        try:
            logger.info(f"ARIMA started for {material}")

            model = ARIMA(train[value_col], order=(5, 1, 0)).fit()
            steps = test_size if test_mode else periods_to_forecast
            forecast = model.forecast(steps=steps)

            if test_mode:
                rmse = np.sqrt(mean_squared_error(test[value_col], forecast))
                mae = mean_absolute_error(test[value_col], forecast)
                mape_val = mape(test[value_col].values.flatten(), forecast.values)
                all_metrics.append({'Model': 'ARIMA', dimension_col: material, 'RMSE': rmse, 'MAE': mae, 'MAPE (%)': mape_val})

            forecast_dates = pd.date_range(start=train.index[-1] + pd.tseries.frequencies.to_offset(freq), periods=steps, freq=freq)
            future_df = pd.DataFrame({date_col: forecast_dates, value_col: forecast.values, dimension_col: material, 'Model': 'ARIMA'})
            all_forecasts.append(future_df)

            train_df = train.copy().reset_index()
            train_df[dimension_col] = material
            train_df['Model'] = 'ARIMA'
            all_train_records.append(train_df)

            if test_mode:
                test_df = test.copy().reset_index()
                test_df[dimension_col] = material
                test_df['Model'] = 'ARIMA'
                all_test_records.append(test_df)

        except Exception as e:
            logger.error(f"ARIMA failed for {material}: {e}", exc_info=True)

    finalize_and_upload(
        df_long, all_forecasts, all_metrics if test_mode else [],
        script_name, append=True,
        all_train_records=all_train_records,
        all_test_records=all_test_records if test_mode else []
    )



def run_mlp_model(df_long, materials, script_name, splits):
    value_col = splits['value_col']
    date_col = splits['date_col']
    dimension_col = splits['dimension_col']
    freq = splits.get('freq', 'MS')
    test_size = splits.get('test_size', 12)
    test_mode = splits['test_mode']
    periods_to_forecast= splits['forecast_periods']

    all_forecasts = []
    all_metrics = []
    all_train_records = []
    all_test_records = []

    for material in materials:
        try:
            '''
            if test_mode:
                # Normal train/test split
                train, test, ts = prepare_train_test_split(df_long, material, splits)

                if train is None:
                    logger.warning(f"Skipping {material} due to insufficient history.")
                    continue

                logger.info(f"MLP started (Test Mode) for {material}")
                forecast_horizon = len(test)
                target_series = train[value_col].values.flatten()

            else:
                # Train on all data
                ts = df_long[df_long[dimension_col] == material][[date_col, value_col]].sort_values(date_col)
                ts = ts.set_index(date_col).resample(freq).sum()
                if len(ts) < periods_to_forecast:
                    logger.warning(f"Skipping {material} due to insufficient history for full training.")
                    continue

                logger.info(f"MLP started (Full Training) for {material}")
                forecast_horizon = periods_to_forecast
                target_series = ts[value_col].values.flatten()
            '''
            train, test, ts = prepare_train_test_split(df_long, material, splits)
            # Print train date range
            print(f"Train date range: {train.index.min().date()} to {train.index.max().date()}")

            # Print test date range
            #print(f"Test date range: {test.index.min().date()} to {test.index.max().date()}")

            logger.info(f"MLP started  for {material} | {test_mode}")
            forecast_horizon = periods_to_forecast
            target_series = train[value_col].values.flatten()


            # Create supervised dataset
            window_size = 12
            X, y = create_supervised(target_series, window_size)

            # Define and fit MLP
            mlp = MLPRegressor(hidden_layer_sizes=(100,), max_iter=1000, random_state=42)
            mlp.fit(X, y)

            # Forecast ahead
            forecast_mlp = []
            last_window = X[-1].copy()
            for _ in range(forecast_horizon):
                next_pred = mlp.predict(last_window.reshape(1, -1))[0]
                forecast_mlp.append(next_pred)
                last_window = np.roll(last_window, -1)
                last_window[-1] = next_pred

            # If test mode, calculate metrics
            if test_mode:
                mlp_rmse = np.sqrt(mean_squared_error(test[value_col], forecast_mlp))
                mlp_mae = mean_absolute_error(test[value_col], forecast_mlp)
                mlp_mape = mape(test[value_col].values.flatten(), forecast_mlp)

                all_metrics.append({
                    'Model': 'MLPRegressor',
                    dimension_col: material,
                    'RMSE': mlp_rmse,
                    'MAE': mlp_mae,
                    'MAPE (%)': mlp_mape
                })

            # Forecast DataFrame
            mlp_future = pd.DataFrame({
                date_col: pd.date_range(
                    start=train.index[-1] + pd.offsets.MonthBegin(1),
                    periods=forecast_horizon,
                    freq=freq
                ),
                value_col: forecast_mlp,
                dimension_col: material,
                'Model': 'MLPRegressor'
            })
            all_forecasts.append(mlp_future)

            # Train actuals
            train_df = train.reset_index()
            train_df[dimension_col] = material
            train_df['Model'] = 'MLPRegressor'
            all_train_records.append(train_df)

            # Test actuals only in test_mode
            if test_mode:
                test_df = test.copy().reset_index()
                test_df[dimension_col] = material
                test_df['Model'] = 'MLPRegressor'
                all_test_records.append(test_df)

        except Exception as e:
            logger.error(f"MLPRegressor failed for {material}: {e}", exc_info=True)

    # Upload results
    finalize_and_upload(
        df_long,
        all_forecasts,
        all_metrics if test_mode else [],  # skip metrics if not in test_mode
        script_name,
        append=True,
        all_train_records=all_train_records,
        all_test_records=all_test_records if test_mode else []  # skip test data if not in test_mode
    )


def run_lstm_model(df_long, materials, script_name, splits):
    value_col = splits['value_col']
    date_col = splits['date_col']
    dimension_col = splits['dimension_col']
    freq = splits.get('freq', 'MS')
    test_size = splits.get('test_size', 12)
    window_size = splits.get('window_size', 12)
    test_mode = splits.get('test_mode', True)  # New flag
    periods_to_forecast = splits.get('periods_to_forecast', 12)

    all_forecasts = []
    all_metrics = []
    all_train_records = []
    all_test_records = []

    for material in materials:
        try:
            logger.info(f"LSTM started for {material} | Test mode: {test_mode}")

            '''
            ts = df_long[df_long[dimension_col] == material][[date_col, value_col]].sort_values(date_col)
            ts = ts.set_index(date_col).resample(freq).sum()

            if len(ts) < window_size + 1:
                logger.warning(f"Skipping {material} due to insufficient history.")
                continue

            if test_mode:
                train = ts[:-test_size]
                test = ts[-test_size:]
            else:
            
                train = ts
                test = None
            '''
            train, test, ts = prepare_train_test_split(df_long, material, splits)
            # Normalize training data
            scaler = MinMaxScaler()
            scaled_train = scaler.fit_transform(train[[value_col]].values)

            # Create supervised learning format
            X_lstm, y_lstm = create_supervised(scaled_train.flatten(), window_size)
            X_lstm = X_lstm.reshape((X_lstm.shape[0], X_lstm.shape[1], 1))

            # Define LSTM model
            model_lstm = Sequential()
            model_lstm.add(LSTM(50, activation='relu', input_shape=(window_size, 1)))
            model_lstm.add(Dense(1))
            model_lstm.compile(optimizer='adam', loss='mse')

            # Train model
            model_lstm.fit(X_lstm, y_lstm, epochs=100, verbose=0)

            # Forecast ahead
            forecast_lstm = []
            input_seq = scaled_train[-window_size:].reshape(1, window_size, 1)
            forecast_steps = test_size if test_mode else periods_to_forecast

            for _ in range(forecast_steps):
                pred = model_lstm.predict(input_seq, verbose=0)[0][0]
                forecast_lstm.append(pred)
                input_seq = np.append(input_seq[:, 1:, :], [[[pred]]], axis=1)

            # Inverse transform predictions
            forecast_lstm_inv = scaler.inverse_transform(
                np.array(forecast_lstm).reshape(-1, 1)
            ).flatten()

            # Metrics only in test mode
            if test_mode and test is not None:
                lstm_rmse = np.sqrt(mean_squared_error(test[value_col], forecast_lstm_inv))
                lstm_mae = mean_absolute_error(test[value_col], forecast_lstm_inv)
                lstm_mape = mape(test[value_col].values.flatten(), forecast_lstm_inv)

                all_metrics.append({
                    'Model': 'LSTM', 
                    dimension_col: material,
                    'RMSE': lstm_rmse, 
                    'MAE': lstm_mae, 
                    'MAPE (%)': lstm_mape
                })

            # Forecast DataFrame
            lstm_future = pd.DataFrame({
                date_col: pd.date_range(
                    start=train.index[-1] + pd.offsets.MonthBegin(1), 
                    periods=forecast_steps, 
                    freq=freq
                ),
                value_col: forecast_lstm_inv,
                dimension_col: material,
                'Model': 'LSTM'
            })
            all_forecasts.append(lstm_future)

            # Train actuals
            train_df = train.reset_index()
            train_df[dimension_col] = material
            train_df['Model'] = 'LSTM'
            all_train_records.append(train_df)

            # Test actuals only in test mode
            if test_mode and test is not None:
                test_df = test.reset_index()
                test_df[dimension_col] = material
                test_df['Model'] = 'LSTM'
                all_test_records.append(test_df)

        except Exception as e:
            logger.error(f"LSTM failed for {material}: {e}", exc_info=True)

    finalize_and_upload(
        df_long,
        all_forecasts,
        all_metrics,
        script_name,
        append=True,
        all_train_records=all_train_records,
        all_test_records=all_test_records if test_mode else []
    )
