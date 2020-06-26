import sys
import os
import time
import datetime
import numpy as np
import pandas as pd
import urllib.request

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import plot_roc_curve
from sklearn.metrics import accuracy_score, classification_report


def grab_data(ticker, path):

    url = 'https://query1.finance.yahoo.com/v7/finance/download/{}?period1=0&period2={}&interval=1wk&events=history'.format(
        ticker, str(time.time())[:-8])

    file = '{}.csv'.format(ticker)
    file_path = '{}/{}.csv'.format(path, ticker)

    while not os.path.exists(file_path):

        r = urllib.request.urlretrieve(
            url, file_path)
        time.sleep(5)

    return file


def calc_rsi(price_data):
    # Calculate the 14 day RSI
    n = 14
    # First make a copy of the data frame twice
    up_df, down_df = price_data[['change_in_price']
                                ].copy(), price_data[['change_in_price']].copy()
    # For up days, if the change is less than 0 set to 0.
    up_df.loc['change_in_price'] = up_df.loc[(
        up_df['change_in_price'] < 0), 'change_in_price'] = 0
    # For down days, if the change is greater than 0 set to 0.
    down_df.loc['change_in_price'] = down_df.loc[(
        down_df['change_in_price'] > 0), 'change_in_price'] = 0
    # We need change in price to be absolute.
    down_df['change_in_price'] = down_df['change_in_price'].abs()
    # Calculate the EWMA (Exponential Weighted Moving Average), meaning older values are given less weight compared to newer values.
    ewma_up = up_df['change_in_price'].transform(
        lambda x: x.ewm(span=n).mean())
    ewma_down = down_df['change_in_price'].transform(
        lambda x: x.ewm(span=n).mean())
    # Calculate the Relative Strength
    relative_strength = ewma_up / ewma_down
    # Calculate the Relative Strength Index
    relative_strength_index = 100.0 - (100.0 / (1.0 + relative_strength))

    return relative_strength_index


def calc_k(price_data):

    n = 14
    # Make a copy of the high and low column.
    low_14, high_14 = price_data[['Low']].copy(), price_data[['High']].copy()
    # Group by symbol, then apply the rolling function and grab the Min and Max.
    low_14 = low_14['Low'].transform(lambda x: x.rolling(window=n).min())
    high_14 = high_14['High'].transform(lambda x: x.rolling(window=n).max())
    # Calculate the Stochastic Oscillator.
    k_percent = 100 * ((price_data['Close'] - low_14) / (high_14 - low_14))

    return k_percent


def calc_r(price_data):


def modelo(price_dataframe):

    # Smoothing
    price_data = price_dataframe[['Date', 'Close', 'High', 'Low', 'Volume']]
    days_out = 7
    price_data_smoothed = price_data[['Close', 'Low', 'High', 'Volume']].transform(
        lambda x: x.ewm(span=days_out).mean())
    smoothed_df = pd.concat(
        [price_data[['Date']], price_data_smoothed], axis=1, sort=False)

    smoothed_df['change_in_price'] = smoothed_df['Close'].diff()
    price_data = smoothed_df

    # Add the info to the data frame.

    price_data['RSI'] = calc_rsi(price_data)

    price_data['k_percent'] = calc_k(price_data)

    price_data['r_percent'] = calc_r(price_data)

    return price_data.head(30)


path = os.getcwd()
price_dataframe = pd.read_csv(grab_data('JBSS3.SA', path))
print(modelo(price_dataframe))
