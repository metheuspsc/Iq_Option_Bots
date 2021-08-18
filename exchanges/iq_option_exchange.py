from datetime import time

import pandas as pd
from iqoptionapi.stable_api import IQ_Option

from exchanges.exchange import Exchange


class IQOptionExchange(Exchange):
    @property
    def api(self) -> IQ_Option:
        api = IQ_Option(self.username, self.password)
        api.connect()
        api.change_balance("PRACTICE")
        return api

    def retry(self):
        while True:
            if not self.api.check_connect():
                print("Erro ao conectar")
                self.api.connect()
            else:
                print("Conectado com Sucesso")
                break
            time.sleep(3)

    @property
    def balance(self) -> float:
        return self.api.get_balance()

    def candles_to_df(self, pair):
        timestamp = self.api.get_server_timestamp()
        velas = []

        for _ in range(5):
            x = self.api.get_candles(pair, 300, 1000, timestamp)
            timestamp = int(x[0]["from"]) - 1
            velas += x

        dataframe = pd.DataFrame(velas)
        dataframe.sort_values(by=["from"], inplace=True, ascending=True)
        dataframe.drop(dataframe.tail(1).index, inplace=True)
        return dataframe[["from", "close", "min", "max", "volume"]]
