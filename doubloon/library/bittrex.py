# -*- coding: UTF-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from bittrex.bittrex import Bittrex, API_V1_1, API_V2_0, BUY_ORDERBOOK, SELL_ORDERBOOK, BOTH_ORDERBOOK
from . import credentials
from . import math_time
import pandas as pd
import wget


class BittrexAPI(object):
    def __init__(self):
        creds = credentials.Credentials()
        self._mathTime = math_time.MathTime()

        api_key = creds.bittrexApiKey
        api_secret = creds.bittrexApiSecret

        self.api_v1_1 = Bittrex(None, None, api_version=API_V1_1)
        self.api_v1_1_authed = Bittrex(api_key, api_secret, api_version=API_V1_1)
        self.api_v2 = Bittrex(None, None, api_version=API_V2_0)
        self.api_v2_authed = Bittrex(api_key, api_secret, api_version=API_V2_0)

    def get_balances(self):
        response = self.api_v2_authed.get_balances()

        if not response.get('result'):
            return None

        results = response['result']
        balances = []

        for data in results:
            if (data['Balance']['Balance'] > 0) or (data['Balance']['Pending'] > 0):
                balance = {**data['Balance'], **data['Currency']}
                balance['BitcoinMarket'] = data['BitcoinMarket']
                balance['EthereumMarket'] = data['EthereumMarket']
                balance['FiatMarket'] = data['FiatMarket']

                balances.append(balance)

        return balances

    def get_markets(self):
        return self.api_v1_1.get_markets()

    def get_currencies(self):
        return self.api_v1_1.get_currencies()

    def get_markets_by_currency(self, symbol):
        return self.api_v1_1.list_markets_by_currency(symbol)

    def get_market_summaries(self):
        response = self.api_v2.get_market_summaries()

        if not response.get('result'):
            return None

        results = response['result']
        markets = []

        for data in results:
            if data['Market']['IsActive']:
                markets.append({**data['Market'], **data['Summary']})

        return markets

    def get_market_summary(self, market):
        response = self.api_v1_1.get_market_summary(market)

        if not response.get('result'):
            return None

        result = response['result'][0]

        return result

    def get_ticker(self, market):
        response = self.api_v1_1.get_ticker(market)

        if not response.get('result'):
            return None

        results = response['result']

        return results

    def get_candles(self, market, tick_interval, as_dataframe=False):
        response = self.api_v2.get_candles(market, tick_interval)

        if not response.get('result'):
            return None

        results = response['result']
        candles = []

        for result in results:
            candle = {}
            candle['open'] = float(result['O'])
            candle['close'] = float(result['C'])
            candle['high'] = float(result['H'])
            candle['low'] = float(result['L'])
            candle['volume'] = float(result['V'])
            candle['base_volume'] = float(result['BV'])
            if as_dataframe:
                candle['timestamp'] = result['T']
            else:
                candle['timestamp'] = self._mathTime.utc_to_local(
                    self._mathTime.bittrex_to_doubloons(result['T']))

            candles.append(candle)

        if as_dataframe:
            df = pd.DataFrame(candles)
            df.reset_index(inplace=True)
            df.set_index("timestamp", inplace=True)

            return df

        return candles

    def get_latest_candle(self, market, tick_interval):
        response = self.api_v2.get_latest_candle(market, tick_interval)

        if not response.get('result'):
            return None

        result = response['result'][0]
        candle = {}

        candle['open'] = float(result['O'])
        candle['close'] = float(result['C'])
        candle['high'] = float(result['H'])
        candle['low'] = float(result['L'])
        candle['volume'] = float(result['V'])
        candle['base_volume'] = float(result['BV'])
        candle['timestamp'] = self._mathTime.utc_to_local(
            self._mathTime.bittrex_to_doubloons(result['T']))

        return candle

    def get_open_orders(self, market=None):
        response = self.api_v1_1_authed.get_open_orders(market)

        if not response.get('result'):
            return None

        results = response['result']

        if len(results) == 0:
            return None

        return results

    def get_order_history(self, market=None):
        response = self.api_v2_authed.get_order_history(market)

        if not response.get('result'):
            return None

        results = response['result']

        if len(results) == 0:
            return None

        return results

    def sell_limit(self, market, quantity, rate):
        response = self.api_v1_1_authed.sell_limit(market, quantity, rate)

        if not response.get('result'):
            return False

        return response['result']['uuid']

    def buy_limit(self, market, quantity, rate):
        response = self.api_v1_1_authed.buy_limit(market, quantity, rate)

        if not response.get('result'):
            return False

        return response['result']['uuid']

    def cancel_order(self, uuid):
        response = self.api_v1_1_authed.cancel(uuid)

        if not response.get('result'):
            return False

        return True

    def get_orderbook(self, market, order_type=None):
        if not order_type:
            depth_type = BOTH_ORDERBOOK

        if order_type == 'buy':
            depth_type = BUY_ORDERBOOK
        elif order_type == 'sell':
            depth_type = SELL_ORDERBOOK

        response = self.api_v1_1.get_orderbook(market, depth_type)

        if not response.get('result'):
            return None

        results = response['result']

        return results

    def get_best_from_orderbook(self, market, order_type=None):
        results = self.get_orderbook(market, order_type)

        if not results:
            return None

        if order_type in ['buy', 'sell']:
            return results[0]

        return ({'buy': results['buy'][0]}, {'sell': results['sell'][0]})

    def get_last_ten_orders(self, market):
        market_history = self.get_market_history(market)

        buys = []
        sells = []

        for order in market_history:
            if order['type'] == 'buy' and len(buys) < 10:
                buys.append(order)

            if order['type'] == 'sell' and len(sells) < 10:
                sells.append(order)

        return {'buy': buys, 'sell': sells}

    def get_market_history(self, market):
        response = self.api_v1_1.get_market_history(market)

        results = response['result']
        history = []

        if not results:
            return None

        for result in results:
            order = {}

            order['complete'] = False
            if result['FillType'] == 'FILL':
                order['complete'] = True

            order['type'] = result['OrderType'].lower()
            order['quantity'] = float(result['Quantity'])
            order['market_price'] = float(result['Price'])
            order['base_price'] = float(result['Total'])
            order['timestamp'] = self._mathTime.utc_to_local(
                self._mathTime.bittrex_to_doubloons(result['TimeStamp']))

            past_hour = self._mathTime.snapshot(hours=1)
            order['recent'] = self._mathTime.doubloon_compare_times(order['timestamp'], past_hour)

            history.append(order)

        history = sorted(history, key=lambda k: (k['timestamp']))

        return history

    def download_logos(self):
        response = self.get_markets()

        if not response.get('result'):
            return False

        results = response['result']

        downloaded = []

        for result in results:
            currency = result['MarketCurrency']
            logourl = result['LogoUrl']
            file = 'static/img/currencies/' + currency + '.png'

            if currency not in downloaded:
                try:
                    print('\nDownloading', currency, 'logo:')
                    wget.download(logourl, file,)
                    print('')
                    downloaded.append(currency)
                except Exception:
                    print('Download Failed!\n')

        print('Done!')
