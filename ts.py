import streamlit as st
import pandas as pd
import sqlite3 as sq
import datetime
from alpha_vantage.timeseries import TimeSeries
from preprocess import preprocessing
import warnings
warnings.filterwarnings("ignore")

# Alpha Vantage API Key
API_KEY = "J4YQ5FHQ5Q0013U"
ts = TimeSeries(key=API_KEY, output_format='pandas')

st.title("Stock Price Prediction")
st.write("Select different stocks, intervals, and periods from the sidebar. Experiment with different models!")

db = sq.connect('stocks.db')

# Get country
query = "SELECT DISTINCT(Country) FROM tkrinfo;"
country = pd.read_sql_query(query, db)
choice_country = st.sidebar.selectbox("Pick country", country)

# Get exchange
query = "SELECT DISTINCT(Exchange) FROM tkrinfo WHERE Country = '" + choice_country + "'"
exchange = pd.read_sql_query(query, db)
choice_exchange = st.sidebar.selectbox("Pick exchange", exchange, index=1)

# Get stock name
query = "SELECT DISTINCT(Name) FROM tkrinfo WHERE Exchange = '" + choice_exchange + "'"
name = pd.read_sql_query(query, db)
choice_name = st.sidebar.selectbox("Pick the Stock", name)

# Get stock ticker
query = "SELECT DISTINCT(Ticker) FROM tkrinfo WHERE Exchange = '" + choice_exchange + "' and Name = '" + choice_name + "'"
ticker_name = pd.read_sql_query(query, db)
ticker_name = ticker_name.loc[0][0]

# Get stock data from Alpha Vantage
try:
    data, meta_data = ts.get_daily(symbol=ticker_name, outputsize='full')
    data = data[::-1]  # Reverse order
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
except Exception as e:
    st.write("❌ Error fetching data from Alpha Vantage:", e)
    db.close()
    st.stop()

# Preprocess data
data = preprocessing(data, '1d')

# Forecast horizon selection
horizon = st.sidebar.slider("Forecast horizon", 1, 30, 5)

# Model selection
model = st.selectbox('Model', ['Simple Exponential Smoothing', 'Holt Model', 'Holt-Winter Model', 'Auto Regressive Model',
                               'Moving Average Model', 'ARMA Model', 'ARIMA Model'])

# Implement different models
if model == 'Simple Exponential Smoothing':
    from SES import SES_model
    alpha_high = st.slider("Alpha_high", 0.0, 1.0, 0.20)
    alpha_low = st.slider("Alpha_low", 0.0, 1.0, 0.25)
    data_final, smap_low, smap_high, optim_alpha_high, optim_alpha_low = SES_model(data, horizon, alpha_high, alpha_low)
    
    st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])
    st.write(f"SMAPE for High: {smap_high}, Optimal Alpha for High: {optim_alpha_high}")
    st.write(f"SMAPE for Low: {smap_low}, Optimal Alpha for Low: {optim_alpha_low}")

elif model == 'Holt Model':
    from SES import Holt_model
    level_high = st.slider("Level High", 0.0, 1.0, 0.20)
    trend_high = st.slider("Trend High", 0.0, 1.0, 0.20)
    level_low = st.slider("Level Low", 0.0, 1.0, 0.20)
    trend_low = st.slider("Trend Low", 0.0, 1.0, 0.20)
    
    data_final, smap_low, smap_high, optim_level_high, optim_level_low, optim_trend_high, optim_trend_low = Holt_model(
        data, horizon, level_high, level_low, trend_high, trend_low)
    
    st.line_chart(data_final[['High', 'Forecast_High', 'Low', 'Forecast_Low']])
    st.write(f"SMAPE for High: {smap_high}, Optimal Level for High: {optim_level_high}, Optimal Trend for High: {optim_trend_high}")
    st.write(f"SMAPE for Low: {smap_low}, Optimal Level for Low: {optim_level_low}, Optimal Trend for Low: {optim_trend_low}")

# Add other models as needed...

db.close()
