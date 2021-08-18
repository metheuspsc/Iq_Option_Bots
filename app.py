import streamlit as st

from bots.rf_bot import RandomForestBot
from exchanges.iq_option_exchange import IQOptionExchange


def image_and_header():
    image = "static/personagem2.png"

    col1, mid, col2 = st.columns([30, 10, 40])
    with col1:
        st.image(image, use_column_width=True)
    with col2:
        st.write("# World's most amazing trading bots!!!")


def core():  # sourcery skip: extract-method
    image_and_header()

    if 'logged' not in st.session_state:
        st.session_state.logged = False

    if not st.session_state.logged:

        with st.sidebar.form("Login"):
            st.session_state.username = st.text_input("Username")
            st.session_state.password = st.text_input("Password", type="password")
            st.session_state.account_type = st.selectbox("Select balance type", ["PRACTICE"])
            st.session_state.exchange_name = st.selectbox("Select Exchange", ["IQ Option"])

            if st.form_submit_button("Login"):

                if st.session_state.exchange_name == "IQ Option":
                    st.session_state.exchange = IQOptionExchange(
                        username=st.session_state.username,
                        password=st.session_state.password,
                        account_type=st.session_state.account_type,
                    )
                else:
                    raise NoExchangeException()
                st.session_state.logged = True

    else:

        # TODO: get pairs available on exchange
        st.session_state.pair = st.sidebar.selectbox("Select asset to trade", ["EURUSD"])
        st.session_state.bot_type = st.sidebar.selectbox("Select Bot Type", ["Random Forests"])
        st.session_state.entry_value = st.sidebar.number_input("Select entry value", 10)
        st.session_state.stop_gain = st.sidebar.number_input("Select stop gain value", 100)
        st.session_state.stop_loss = st.sidebar.number_input("Select stop loss value", 100)

        col1,col2 = st.sidebar.columns(2)

        if col1.button("Run Bot!"):

            if st.session_state.bot_type == "Random Forests":
                bot = RandomForestBot(
                    exchange=st.session_state.exchange,
                    entry_value=st.session_state.entry_value,
                    stop_gain=st.session_state.stop_gain,
                    stop_loss=st.session_state.stop_loss,
                    pair=st.session_state.pair,
                )
            else:
                raise NoBotException()

            bot.run()

        if col2.button("Return..."):
            st.session_state.logged = False


class NoExchangeException(Exception):
    pass


class NoBotException(Exception):
    pass


if __name__ == "__main__":
    core()
