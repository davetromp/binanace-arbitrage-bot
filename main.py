#!/usr/bin/python3
from binance.client import Client
import pandas as pd
import time

# http://python-binance.readthedocs.io/en/latest/index.html

"""
Simple arbitrage script on Binance.
Arbitraging over BTC and ETH pairs.
Set trade size value at TRADESIZE.
Set threshold value for minimal disparicy needed to trigger a trade at THRESHOLD.
Set fee value for the percentage of fee to take into account at FEE.
Set a list of coins to trade at COINS.
If the list is left empty, all available coins will be scanned for arbitrage oportunities.
Set timeframe value at TF in seconds for trade check interval.

Requirements: pandas, python-binance
"""

TRADESIZE = 0.0015
THRESHOLD = 0.5
FEE = 0.3
COINS = []
TF = 15

API_KEY = "PUT YOUR KEY HERE"
API_SECRET = "PUT YOUR SECRET HERE"

client = Client(API_KEY, API_SECRET)


def check_arb_btc_coin_eth_btc(df, coins, threshold=0.5, fee=0.3):
    highest_profit = (None, 0)
    for coin in coins:
        try:
            base = float(df['price']['{}BTC'.format(coin)])
            arb = float(df['price']['{}ETH'.format(coin)]) * \
                float(df['price']['ETHBTC'])
            dif = arb - base
            diff = ((arb/base) - 1) * 100.0
            profit = diff - fee
            if profit > threshold:
                print(coin)
                print("Buy {} against BTC".format(coin))
                print("Value in BTC                 : {}".format(base))
                print("Sell {} against ETH".format(coin))
                print("Value in BTC from ETH        : {}".format(arb))
                print("Sell ETH back to BTC for diff: {}".format(dif))
                print("Value diff in percent        : {}".format(diff))
                print("Profit minus fees in percent : {}%".format(profit))
                print("")
                if profit > highest_profit[1]:
                    highest_profit = (coin, profit)
        except Exception as e:
            pass
    return highest_profit


def setqty(qty, coin):
    info = client.get_symbol_info(coin)
    minQty = float(info['filters'][1]['minQty'])
    if qty < minQty:
        qty = minQty
    else:
        qty = qty - (qty % minQty)
    return qty


def excecute_btc_coin_eth_btc(coin, btcvalue, df):
    ethsymbol = '{}ETH'.format(coin)
    ethsymbolpricestring = df['price'][ethsymbol]
    ethsymbolprice = float(df['price'][ethsymbol])

    btcsymbol = '{}BTC'.format(coin)
    pricestring = df['price'][btcsymbol]
    price = float(df['price'][btcsymbol])
    qty = round(float(btcvalue) / float(price))
    qty = setqty(qty, btcsymbol)
    buyvalue = qty * price
    if buyvalue < btcvalue * 1.1:

        print("Buying {} of {} at {}".format(qty, btcsymbol, pricestring))
        print("For a total of {} BTC".format(buyvalue))
        print(client.order_market_buy(
            symbol=btcsymbol,
            quantity=qty)['status'])

        print("Selling {} of {} at {}".format(
            qty, ethsymbol, ethsymbolpricestring))
        print("For a total of {} ETH".format(qty * ethsymbolprice))
        print(client.order_market_sell(
            symbol=ethsymbol,
            quantity=qty)['status'])

        rebalanceqty = setqty(ethsymbolprice * qty, 'ETHBTC')
        ethbtcpricestring = df['price']['ETHBTC']
        ethbtcprice = float(df['price']['ETHBTC'])
        sellvalue = rebalanceqty * ethbtcprice
        print("Selling {} of ETHBTC at {}".format(
            rebalanceqty, ethbtcpricestring))
        print("For a total of {} BTC".format(sellvalue))
        print("For a profit of {} BTC".format(sellvalue - buyvalue))
        print(client.order_market_sell(
            symbol='ETHBTC',
            quantity=rebalanceqty)['status'])

        balance = client.get_asset_balance(asset='ETH')
        ethbal = float(balance['free']) * ethbtcprice
        balance = client.get_asset_balance(asset='BTC')
        btcbal = float(balance['free'])
        print("---> final btc + eth balance:", ethbal + btcbal)

    else:
        print("rounded value to high")

        print("Buying {} of {} at {}".format(qty, btcsymbol, price))
        print("For a total of {} BTC".format(buyvalue))
        ethsymbol = '{}ETH'.format(coin)
        ethsymbolprice = float(df['price'][ethsymbol])
        print("Selling {} of {} at {}".format(qty, ethsymbol, price))
        print("For a total of {} ETH".format(qty * ethsymbolprice))
        rebalanceqty = setqty(ethsymbolprice * qty, 'ETHBTC')
        ethbtcprice = float(df['price']['ETHBTC'])
        sellvalue = rebalanceqty * ethbtcprice
        print("Selling {} of ETHBTC at {}".format(rebalanceqty, ethbtcprice))
        print("For a total of {} BTC".format(sellvalue))
        print("For a profit of {} BTC".format(sellvalue - buyvalue))


def arb():
    prices = client.get_all_tickers()
    if len(COINS) == 0:
        coins = []
        for pair in prices:
            coin = pair['symbol'].replace('BTC', '').replace(
                'ETH', '').replace('BNB', '')
            coins.append(coin)
        coins = list(set(coins))
    else:
        coins = COINS
    df = pd.DataFrame(prices).set_index(['symbol'])
    hprofitcoin = check_arb_btc_coin_eth_btc(
        df, coins, threshold=THRESHOLD, fee=FEE)[0]
    if hprofitcoin:
        print("")
        print("###########")
        print("highest_profit:", hprofitcoin)
        print("###########")
        excecute_btc_coin_eth_btc(hprofitcoin, TRADESIZE, df)


def main():
    c = 1
    while True:
        try:
            arb()
        except Exception as e:
            print(str(e))
        c += 1
        time.sleep(TF)


main()
