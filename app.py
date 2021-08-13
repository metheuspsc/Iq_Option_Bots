import streamlit as st

from bots.rf_bot import RandomForestBot
from exchanges.iq_option_exchange import IQOptionExchange
import base64


def core():
    image = "static/personagem2.png"

    col1, mid, col2 = st.columns([30, 10, 40])
    with col1:
        st.image(image, use_column_width=True)
    with col2:
        st.write("# World's most amazing trading bots!!!")

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    pair = st.sidebar.selectbox("Select pair to trade", ["EURUSD"])
    account_type = st.sidebar.selectbox("Select balance type", ["PRACTICE"])
    exchange_name = st.sidebar.selectbox('Select Exchange', ["IQ Option"])
    bot_type = st.sidebar.selectbox('Select Bot Type', ["Random Forests"])
    entry_value = st.sidebar.number_input('Select entry value', 10)
    stop_gain = st.sidebar.number_input('Select stop gain value', 100)
    stop_loss = st.sidebar.number_input('Select stop loss value', 100)

    if st.sidebar.button("Run"):

        if exchange_name == "IQ Option":
            exchange = IQOptionExchange(
                username=username,
                password=password,
                account_type=account_type,
                pair=pair,
            )
        else:
            raise NoExchangeException()

        if bot_type == "Random Forests":
            bot = RandomForestBot(
                exchange=exchange, entry_value=entry_value, stop_gain=stop_gain, stop_loss=stop_loss
            )
        else:
            raise NoBotException()

        bot.run()


class NoExchangeException(Exception):
    pass


class NoBotException(Exception):
    pass


if __name__ == "__main__":
    core()
