import sys
from iqoptionapi.stable_api import IQ_Option
import time
from datetime import datetime
from datetime import timedelta
from dateutil import tz

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import plot_roc_curve
from sklearn.metrics import accuracy_score, classification_report


def timestamp_converter(x):  # Função para converter timestamp
    hora = datetime.strptime(datetime.utcfromtimestamp(
        x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))

    return hora


API = IQ_Option('Login', 'Senha')
API.connect()
API.change_balance('PRACTICE')
par = 'GBPJPY'

while True:
    if API.check_connect() == False:
        print('Erro ao conectar')
        API.connect
    else:
        print('Conectado com Sucesso')
        break
    time.sleep(3)


def preview():

    timestamp = API.get_server_timestamp()
    hora = timestamp_converter(timestamp)
    velas = []

    for i in range(20):
        X = API.get_candles(par, 60, 1000, timestamp)
        timestamp = int(X[0]['from'])-1
        velas += X

    price_data = pd.DataFrame(velas)
    price_data.sort_values(by=['from'], inplace=True, ascending=True)
    price_data = price_data[['from', 'close', 'min', 'max', 'volume']]
    price_data['change_price'] = price_data['close'].diff()

    # Calculate RSI
    n = 5
    up_df, down_df = price_data[['change_price']
                                ].copy(), price_data[['change_price']].copy()
    up_df.loc['change_price'] = up_df.loc[(
        up_df['change_price'] < 0), 'change_price'] = 0
    down_df.loc['change_price'] = down_df.loc[(
        down_df['change_price'] > 0), 'change_price'] = 0
    down_df['change_price'] = down_df['change_price'].abs()
    ewma_up = up_df['change_price'].transform(lambda x: x.ewm(span=n).mean())
    ewma_down = down_df['change_price'].transform(
        lambda x: x.ewm(span=n).mean())
    relative_strength = ewma_up / ewma_down
    relative_strength_index = 100.0 - (100.0 / (1.0 + relative_strength))

    # Calculate the Stochastic Oscillator
    n = 14
    low_14, high_14 = price_data[['min']].copy(), price_data[['max']].copy()
    low_14 = low_14['min'].transform(lambda x: x.rolling(window=n).min())
    high_14 = high_14['max'].transform(lambda x: x.rolling(window=n).max())
    k_percent = 100 * ((price_data['close'] - low_14) / (high_14 - low_14))

    # Calculate the Williams %R
    n = 14
    low_14, high_14 = price_data[['min']].copy(), price_data[['max']].copy()
    low_14 = low_14['min'].transform(lambda x: x.rolling(window=n).min())
    high_14 = high_14['max'].transform(lambda x: x.rolling(window=n).max())
    r_percent = ((high_14 - price_data['close']) / (high_14 - low_14)) * - 100

    # Calculate the MACD
    ema_26 = price_data['close'].transform(lambda x: x.ewm(span=26).mean())
    ema_12 = price_data['close'].transform(lambda x: x.ewm(span=12).mean())
    macd = ema_12 - ema_26

    # Calculate the EMA
    ema_9_macd = macd.ewm(span=9).mean()

    # Calculate the Rate of Change in the Price, and store it in the Data Frame.
    n = 9
    price_data['Price_Rate_Of_Change'] = price_data['close'].transform(
        lambda x: x.pct_change(periods=n))
    price_data['RSI'] = relative_strength_index
    price_data['k_percent'] = k_percent
    price_data['r_percent'] = r_percent
    price_data['MACD'] = macd
    price_data['MACD_EMA'] = ema_9_macd
    
    # Predictions
    close_groups = price_data['close']
    close_groups = close_groups.transform(lambda x: np.sign(x.diff()))
    price_data['Prediction'] = close_groups
    price_data.loc[price_data['Prediction'] == 0.0] = 1.0

    # Any row that has a `NaN` value will be dropped.
    price_data = price_data.dropna()

    # Grab our X & Y Columns.
    X_Cols = price_data[['RSI', 'k_percent', 'r_percent',
                         'MACD', 'MACD_EMA', 'Price_Rate_Of_Change']]
    Y_Cols = price_data['Prediction']

    # Split X and y into X_
    X_train, X_test, y_train, y_test = train_test_split(
        X_Cols, Y_Cols, random_state=0)

    # Create a Random Forest Classifier
    rand_frst_clf = RandomForestClassifier(
        n_estimators=100, oob_score=True, criterion="gini", random_state=0)

    # Fit the data to the model
    rand_frst_clf.fit(X_train, y_train)

    # Make predictions
    y_pred = rand_frst_clf.predict(X_test)

    print('Assertividade (%): ', accuracy_score(
        y_test, rand_frst_clf.predict(X_test), normalize=True) * 100.0)

    tradeMap = {-1.0: "put", 1.0: "call", 0.0: "call"}
    teste = timestamp_converter(price_data['from'].iloc[-1])
    teste = teste + timedelta(seconds=60)
    result = pd.DataFrame([teste+timedelta(seconds=60*i) for i in range(len(y_pred))],
                          [tradeMap[y_pred[i]] for i in range(len(y_pred))])

    return result


def banca():
    return API.get_balance()


valor_entrada = 0
valor = 0
lucro = 0

# Realiza 5 entradas baseado na ultima previsão do modelo, após isso realiza uma nova previsão
while True:

    ids = []
    df = preview().head(5)

    for row in df.itertuples():
        valor_entrada = float(int(banca()) // 10)

        bs = row[0]
        sinal = row[1]

        while True:

            tempo_servidor = timestamp_converter(
                API.get_server_timestamp())

            if tempo_servidor + timedelta(seconds=3) == sinal:
                valor_entrada = float(int(banca()) // 10)
                print('Entrou', bs, sinal, '\nEntrada:', valor_entrada)
                status, id = API.buy_digital_spot(
                    par, valor_entrada, bs, 1)
                ids.append(id)
                time.sleep(1)

            if tempo_servidor > sinal:
                print('Próximo Sinal')
                break
