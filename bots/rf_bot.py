import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from bots.process import DataProcessor
from bots.trading_bot import TradingBot


class RandomForestBot(TradingBot):
    def sinal(self, df):
        df = DataProcessor(df).df
        return self.predict_rf(df)

    @staticmethod
    def model_params(df):
        today = df.tail(1)[
            [
                "rsi",
                "k_percent",
                "r_percent",
                "macd",
                "macd_ema",
                "price_rate_of_change",
                "on_balance_volume",
            ]
        ]
        df.dropna(inplace=True)

        x_cols = df[
            [
                "rsi",
                "k_percent",
                "r_percent",
                "macd",
                "macd_ema",
                "price_rate_of_change",
                "on_balance_volume",
            ]
        ]
        y_cols = df["predictions"]

        x_train, x_test, y_train, y_test = train_test_split(
            x_cols, y_cols, random_state=0, shuffle=False
        )

        return today, x_cols, y_cols, x_train, x_test, y_train, y_test

    @staticmethod
    def rf_metrics(model, y_test, y_pred, x_cols):
        accuracy = accuracy_score(y_test, y_pred, normalize=True) * 100.0

        st.info(f"Assertividade (%): {accuracy}")

        feature_imp = pd.Series(
            model.feature_importances_, index=x_cols.columns
        ).sort_values(ascending=False)

        print(feature_imp)

    def predict_rf(self, df):
        rand_frst_clf = RandomForestClassifier(
            n_estimators=100, oob_score=True, criterion="gini", random_state=0
        )

        today, x_cols, y_cols, x_train, x_test, y_train, y_test = self.model_params(df)

        rand_frst_clf.fit(x_train, y_train)

        y_pred = rand_frst_clf.predict(x_test)

        accuracy = accuracy_score(y_test, y_pred, normalize=True) * 100.0

        next = rand_frst_clf.predict_proba(today)[0]

        st.info(
            f"Assertividade (%): {accuracy} Previsão (%): Baixa :{next[0]}, Alta :{next[1]}"
        )

        return "put" if next[0] > next[1] else "call"

    @staticmethod
    def get_random_grid():
        n_estimators = list(range(200, 2000, 200))

        max_features = ["auto", "sqrt", None, "log2"]

        max_depth = list(range(10, 110, 10))
        max_depth.append(None)

        min_samples_split = [2, 5, 10, 20, 30, 40]

        min_samples_leaf = [1, 2, 7, 12, 14, 16, 20]

        bootstrap = [True, False]

        return {
            "n_estimators": n_estimators,
            "max_features": max_features,
            "max_depth": max_depth,
            "min_samples_split": min_samples_split,
            "min_samples_leaf": min_samples_leaf,
            "bootstrap": bootstrap,
        }
