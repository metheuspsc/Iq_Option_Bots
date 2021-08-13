from iqoptionapi.stable_api import IQ_Option
import time
import json
from datetime import datetime
from dateutil import tz
import sys


def stop(lucro, gain, loss):
    if lucro <= float("-" + str(abs(loss))):
        print("Stop Loss batido!")
        sys.exit()

    if lucro >= float(abs(gain)):
        print("Stop Gain Batido!")
        sys.exit()


def Martingale(valor, payout):
    lucro_esperado = valor * payout
    perca = float(valor)

    while True:
        if round(valor * payout, 2) > round(abs(perca) + lucro_esperado, 2):
            return round(valor, 2)
            break
        valor += 0.01


def Payout(par):
    API.subscribe_strike_list(par, 1)
    while True:
        d = API.get_digital_current_profit(par, 1)
        if d != False:
            d = round(int(d) / 100, 2)
            break
        time.sleep(1)
    API.unsubscribe_strike_list(par, 1)

    return d


API = IQ_Option("Login", "Senha")  # Entrar Login e Senha
API.connect()
API.change_balance("REAL")  # Real ou Practice

while True:
    if API.check_connect() == False:
        print("Erro ao conectar")
        API.connect
    else:
        print("Conectado com Sucesso")
        break
    time.sleep(3)


def timestamp_converter(x):  # Função para converter timestamp
    hora = datetime.strptime(
        datetime.utcfromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"
    )
    hora = hora.replace(tzinfo=tz.gettz("GMT"))

    return hora


def banca():
    return API.get_balance()


print("Banca:", banca())  # pega valor da Banca
par = "USDJPY"
valor_entrada = (
    float(int(banca()) // 10) if int(banca()) > 20 else 2
)  # inicia entradas com 10% da banca ou 2 (mínimo possível)
valor_entrada_b = float(valor_entrada)

martingale = int(1)
martingale += 1

stop_loss = float(int(banca()) // 5)
print("Stop Loss:", stop_loss)
stop_gain = float(int(banca()) // 2)
print("Stop Gain:", stop_gain)

lucro = 0
valor = 0
payout = Payout(par)

while True:
    teste = timestamp_converter(API.get_server_timestamp())
    minutos = float((teste.strftime("%M.%S"))[1:])
    entrar = True if (minutos >= 4.57 and minutos <= 5) or minutos >= 9.57 else False

    if entrar:
        print("\n\nIniciando Trade!", "\nData:", str(teste)[:-6])

        if valor > 0:  # Wins consecutivos adicionam metade do Gain na próxima entrada

            valor_entrada = float(int(banca()) // 10) + round(valor // 2, 2)

        else:
            valor_entrada = float(int(banca()) // 10)

        print("Entrada:", valor_entrada)
        dir = False
        inverte = False
        print("Verificando cores..")  # Aplica Estratégia MHI Potencializada

        velas = API.get_candles(par, 60, 10, API.get_server_timestamp())

        velas[2] = (
            "g"
            if velas[2]["open"] < velas[2]["close"]
            else "r"
            if velas[2]["open"] > velas[2]["close"]
            else "d"
        )
        velas[3] = (
            "g"
            if velas[3]["open"] < velas[3]["close"]
            else "r"
            if velas[3]["open"] > velas[3]["close"]
            else "d"
        )
        velas[4] = (
            "g"
            if velas[4]["open"] < velas[4]["close"]
            else "r"
            if velas[4]["open"] > velas[4]["close"]
            else "d"
        )
        velas[5] = (
            "g"
            if velas[5]["open"] < velas[5]["close"]
            else "r"
            if velas[5]["open"] > velas[5]["close"]
            else "d"
        )
        velas[6] = (
            "g"
            if velas[6]["open"] < velas[6]["close"]
            else "r"
            if velas[6]["open"] > velas[6]["close"]
            else "d"
        )
        velas[7] = (
            "g"
            if velas[7]["open"] < velas[7]["close"]
            else "r"
            if velas[7]["open"] > velas[7]["close"]
            else "d"
        )
        velas[8] = (
            "g"
            if velas[8]["open"] < velas[8]["close"]
            else "r"
            if velas[8]["open"] > velas[8]["close"]
            else "d"
        )
        velas[9] = (
            "g"
            if velas[9]["open"] < velas[9]["close"]
            else "r"
            if velas[9]["open"] > velas[9]["close"]
            else "d"
        )

        cores1 = velas[2] + " " + velas[3] + " " + velas[4]

        if cores1.count("g") > cores1.count("r") and cores1.count("d") == 0:
            next = "r"
            if velas[5] != next and velas[6] != next:
                inverte = True
            else:
                inverte = False

        if cores1.count("r") > cores1.count("g") and cores1.count("d") == 0:
            next = "g"
            if velas[5] != next and velas[6] != next:
                inverte = True
            else:
                inverte = False

        cores2 = velas[7] + " " + velas[8] + " " + velas[9]

        if 3 > cores2.count("g") > cores2.count("r") and cores2.count("d") == 0:
            if not inverte:
                dir = "put"
            else:
                dir = "call"

        if 3 > cores2.count("r") > cores2.count("g") and cores2.count("d") == 0:
            if not inverte:
                dir = "call"
            else:
                dir = "put"

        if cores2.count("d") > 0:
            dir = False

        print(
            "Primeiro Quadrante:",
            cores1,
            "\nCandle:",
            velas[5],
            velas[6],
            "\nSegundo Quadrante:",
            cores2,
            "\nInverteu?",
            inverte,
            "\nSentido:",
            dir,
        )

        if dir:

            for i in range(martingale):

                status, id = API.buy_digital_spot(par, valor_entrada, dir, 1)

                if status:
                    while True:
                        status, valor = API.check_win_digital_v2(id)

                        if status:
                            valor = (
                                valor
                                if valor > 0
                                else float("-" + str(abs(valor_entrada)))
                            )
                            lucro += round(valor, 2)

                            print("Resultado: ", end="")
                            print(
                                "WIN /" if valor > 0 else "LOSS /",
                                round(valor, 2),
                                "/",
                                round(lucro, 2),
                                ("/ " + str(i) + " GALE" if i > 0 else ""),
                            )

                            valor_entrada = Martingale(
                                valor_entrada_b // 2, payout
                            )  # Martingale com metade do valor de entrada * o payout

                            stop(lucro, stop_gain, stop_loss)

                            break

                    if valor > 0:
                        break

                else:
                    print("\nERRO AO REALIZAR ORDEM\n\n")

        else:
            print("Analise Inconclusiva, foram encontrados candles neutros")
            time.sleep(5)
            entrar = False
