import sys
from iqoptionapi.stable_api import IQ_Option
import time
from datetime import datetime
from datetime import timedelta
from dateutil import tz

import numpy as np
import pandas as pd

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


API = IQ_Option('matheuspessoax@gmail.com', 'xereca123')
API.connect()
API.change_balance('PRACTICE')
par = 'EURUSD'

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

    for i in range(10):
        X = API.get_candles(par, 300, 1000, timestamp)
        timestamp = int(X[0]['from'])-1
        velas += X

    price_data = pd.DataFrame(velas)
    price_data.sort_values(by=['from'], inplace=True, ascending=True)
    price_data.drop(price_data.tail(1).index, inplace=True)
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
    # price_data['low_14'] = low_14
    # price_data['high_14'] = high_14
    price_data['k_percent'] = k_percent
    price_data['r_percent'] = r_percent
    price_data['MACD'] = macd
    price_data['MACD_EMA'] = ema_9_macd

    # pd.DataFrame(price_data).to_csv('price_data.csv', index_label=False)

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

    tradeMap = {-1.0: "put", 1.0: "call", 0.0: "Null"}
    teste = timestamp_converter(price_data['from'].iloc[-1])
    print('ultimo candle dentro do modelo:',
          str(teste)[-11:-6], tradeMap[price_data['Prediction'].iloc[-1]])

    # Fechamento da última vela

    teste = teste + timedelta(seconds=300)
    d = {'From': [teste+timedelta(seconds=300*i) for i in range(len(y_pred))], 'Pred': [
        tradeMap[y_pred[i]] for i in range(len(y_pred))]}
    result = pd.DataFrame(d)

    return result


def stop_check(lucro, gain, loss):
    if lucro <= float('-' + str(abs(loss))):
        print('Stop Loss batido!')
        sys.exit()

    if lucro >= float(abs(gain)):
        print('Stop Gain Batido!')
        sys.exit()


def banca():
    return API.get_balance()


valor_entrada = 0
stop_loss = float(int(banca()) // 5)
stop_gain = float(int(banca()) // 2)
lucro = 0

while True:

    valor = 0
    erro = False
    df = preview().head(2)
    print(df)
    ult_tempo = API.get_server_timestamp()

    for row in df.itertuples():
        valor_entrada = float(int(banca()) // 10)
        bs = row[2]
        sinal = row[1]

        while True:

            tempo_servidor = timestamp_converter(
                API.get_server_timestamp())

            if tempo_servidor + timedelta(seconds=2) == sinal:

                ult_vela = API.get_candles(
                    par, 300, 1, API.get_server_timestamp())
                ult_vela = 'call' if ult_vela[0]['open'] < ult_vela[0][
                    'close'] else 'put' if ult_vela[0]['open'] > ult_vela[0]['close'] else 'Nulo'

                print('Ultimo Fechamento:', ult_vela)
                print('Teste:', df['Pred'].iloc[0])

                if ult_vela == df['Pred'].iloc[0]:

                    valor_entrada = float(int(banca()) // 10)
                    print('Entrou', bs, sinal, '\nEntrada:', valor_entrada)
                    status, id = API.buy_digital_spot(
                        par, valor_entrada, bs, 5)

                    if status:
                        while True:

                            status, valor = API.check_win_digital_v2(id)

                            if status:
                                valor = valor if valor > 0 else float(
                                    '-' + str(abs(valor_entrada)))
                                lucro += round(valor, 2)

                                print('\nWIN:' if valor > 0 else '\nLOSS:', round(valor, 2), '\nLucro Líquido:',
                                      round(lucro, 2))

                                stop_check(lucro, stop_gain, stop_loss)

                                break
                    else:
                        print('\nERRO AO REALIZAR ORDEM\n\n')

                else:
                    print('Modelo Errou Primeira Previsão')
                    erro = True

            if tempo_servidor > sinal:
                break

            elif erro:
                break

    if valor < 0 or erro:
        print('Modelo Errou, Recalculando...')
        time.sleep(10)
