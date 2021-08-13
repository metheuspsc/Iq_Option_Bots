import numpy as np
import pandas as pd


class DataProcessor:
    def __init__(self, df):
        self.df = df
        self.process()

    def process(self):
        self.calc_price_change()
        self.calc_rsi()
        self.calc_k_r()
        self.calc_macd()

        self.calc_prc()
        self.calc_obv()
        self.calc_predictions()

    def calc_price_change(self):
        self.df["price_change"] = self.df["close"].diff()

    def calc_rsi(self):
        n = 5
        delta = self.df[["price_change"]]
        up_df, down_df = delta.copy(), delta.copy()

        up_df[up_df < 0] = 0
        down_df[down_df > 0] = 0

        ewma_up = up_df.ewm(span=n).mean()
        ewma_down = down_df.abs().ewm(span=n).mean()

        rs = ewma_up / ewma_down
        self.df["rsi"] = 100.0 - (100.0 / (1.0 + rs))

    def calc_k_r(self):
        n = 14

        high_14 = self.df["max"].rolling(14).max()
        low_14 = self.df["min"].rolling(14).min()

        self.df["k_percent"] = 100 * ((self.df["close"] - low_14) / (high_14 - low_14))
        self.df["r_percent"] = (
            (high_14 - self.df["close"]) / (high_14 - low_14)
        ) * -100

    def calc_macd(self):
        ema_26 = self.df["close"].ewm(span=26).mean()
        ema_12 = self.df["close"].ewm(span=12).mean()
        self.df["macd"] = ema_12 - ema_26
        self.df["macd_ema"] = self.df["macd"].ewm(span=9).mean()

    def calc_prc(self):
        self.df["price_rate_of_change"] = self.df["close"].pct_change(periods=9)

    def calc_predictions(self):
        close_groups = self.df["close"]
        close_groups = close_groups.transform(lambda x: np.sign(x.diff()))
        close_groups.loc[close_groups == 0.0] = 1.0
        close_groups = close_groups.shift(periods=-1)
        self.df["predictions"] = close_groups

    def calc_obv(self):
        volume = self.df["volume"]
        change = self.df["price_change"]
        prev_obv = 0
        obv_values = []

        for i, j in zip(change, volume):
            if i > 0:
                current_obv = prev_obv + j
            elif i < 0:
                current_obv = prev_obv - j
            else:
                current_obv = prev_obv

            prev_obv = current_obv
            obv_values.append(current_obv)

        self.df["on_balance_volume"] = pd.Series(
            obv_values, index=self.df.index
        ).reset_index(level=0, drop=True)
