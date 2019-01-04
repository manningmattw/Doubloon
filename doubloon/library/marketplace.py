from doubloon.library import bittrex
from doubloon.library import math_time
from doubloon.models import Settings
from doubloon.models import ForcedSell
from time import sleep


class Marketplace(object):
    def __init__(self):
        self._bittrex = bittrex.BittrexAPI()
        self._mathTime = math_time.MathTime()

        self.base_currency = str(Settings.objects.get(setting='base_currency').value)
        self.bases = eval(Settings.objects.get(setting='safety_currencies').value)

        self.wallets = self.check_balances()

    @property
    def buy_allowance(self):
        _diversify = self.diversify()

        if _diversify['allowed'] == 0:
            return 0

        return _diversify['available']

    @property
    def skip_selling(self):
        if len([x for x in self.wallets if x['symbol'] not in self.bases]) == 0:
            return True

        return False

    def buy_limit(self, market, base_price, log=False):
        orderbook = self._bittrex.get_best_from_orderbook(market, 'sell')

        if not orderbook:
            return False

        current_price = orderbook['Rate']
        quantity = float('%.8f' % ((base_price * .9975) / current_price))

        if log:
            print('\n    Cost in ' + self.base_currency + ':       %.8f' % base_price)
            print('    Quantity:          %.8f' % quantity)
            print('    Best Offer Price:  %.8f' % current_price)
            print('')

        buying = self._bittrex.buy_limit(market, quantity, current_price)

        if buying:
            return {'price': current_price, 'quantity': quantity}

        return False

    def check_balances(self):
        base_pending = self.get_base_pending()
        balances = self._bittrex.get_balances()
        wallets = []

        for balance in balances:
            value = balance['Available']
            symbol = balance['Currency']
            add = {
                'balance': value,
                'symbol': symbol}

            market = None

            if symbol not in self.bases:
                if self.base_currency == 'BTC':
                    market = balance['BitcoinMarket']['MarketName']

                if self.base_currency == 'ETH':
                    market = balance['EthereumMarket']['MarketName']

            elif symbol == self.base_currency:
                add['balance'] += base_pending

                if balance['FiatMarket']:
                    market = balance['FiatMarket']['MarketName']

            add['market'] = market
            wallets.append(add)

        wallets = sorted(wallets, key=lambda k: (k['balance']))

        return wallets

    def check_for_open_orders(self):
        open_orders = self._bittrex.get_open_orders()

        orders = {
            'pending': [],
            'cancelled': [],
            'reorder': []}

        if open_orders:
            for order in open_orders:
                opened_for = self._mathTime.minutes(self._mathTime.bittrex_to_doubloons(order['Opened']))
                cancelled = order['CancelInitiated']
                uuid = order['OrderUuid']
                price = order['Limit']
                market = order['Exchange']
                quantity = order['Quantity']
                is_buy = 'BUY' in order['OrderType']
                is_sell = 'SELL' in order['OrderType']
                is_automation_trade = True

                manual_sells = ForcedSell.objects.filter(uuid=uuid)

                if len(manual_sells) > 0:
                    is_automation_trade = False

                market_summary = self._bittrex.get_market_summary(market)
                current_price = market_summary['Last']

                reorder = False
                cancel = False

                if is_sell and is_automation_trade:
                    reorder = (current_price > price) and (not cancelled)
                    cancel = (current_price < price) and (not cancelled)

                if is_buy and is_automation_trade:
                    cancel = all([
                        current_price > price,
                        not cancelled,
                        opened_for >= 2])

                if cancel:
                    self._bittrex.cancel_order(uuid)
                    orders['cancelled'].append(order)

                if reorder:
                    self._bittrex.cancel_order(uuid)
                    orders['reorder'].append({
                        'market': market,
                        'quantity': quantity})
                if not cancel and not reorder:
                    orders['pending'].append(order)

        return orders

    def diversify(self):
        wallets = [x for x in self.wallets if x['market']]
        wallets = [x for x in wallets if self.base_currency == x['market'].split('-')[0]]

        available = next(iter([x['balance'] for x in self.wallets if x['symbol'] == self.base_currency]), 0)
        active = 0
        count = 0

        for wallet in wallets:
            recent_buy_order = self.get_buy_orders(wallet['market'])
            active += recent_buy_order['base_price']
            count += 1

        i = self.max_active_trades
        found = False

        while (i > 0) and (not found):
            test_allowed = (available + active) / i

            if (test_allowed >= self.min_trade_allowed):
                found = True
            else:
                i += -1

        allowed = i - count

        if not found or allowed <= 0:
            return {'available': 0, 'allowed': 0}

        available = available / allowed

        if available < self.min_trade_allowed:
            return {'available': 0, 'allowed': allowed}

        if available >= self.max_trade_allowed:
            available = self.max_trade_allowed

        return {'available': available, 'allowed': allowed}

    def get_base_pending(self):
        open_orders = self._bittrex.get_open_orders()
        base_pending = 0.0

        if not open_orders:
            open_orders = []

        for order in open_orders:
            price = order['Limit']
            quantity = order['Quantity']

            base_pending += price * quantity * .9975

        return base_pending

    def get_buy_orders(self, market=None):
        order_history = self._bittrex.get_order_history(market)
        order_history = [x for x in order_history if 'BUY' in x['OrderType']]

        buy_orders = []

        for order in order_history:
            this_market = order['Exchange']
            base = market.split('-')[0]
            currency = market.split('-')[1]
            quantity = order['Quantity']
            market_price = order['Limit']
            base_price = order['Price'] + order['Commission']

            add = {
                'market': this_market,
                'base': base,
                'currency': currency,
                'market_price': market_price,
                'quantity': quantity,
                'base_price': base_price,
                'closed': order['Closed']}

            buy_orders.append(add)

        if buy_orders == []:
            return None

        only_recent = {}

        for order in buy_orders:
            this_market = order['market']
            closed = order['closed']

            if not only_recent.get(this_market):
                only_recent[this_market] = order
            else:
                recent_closed = only_recent[this_market]['closed']

                if self._mathTime.bittrex_compare_times(closed, recent_closed):
                    only_recent[this_market] = order

        if only_recent == {}:
            return None

        if market:
            return only_recent[market]

        recents = []

        for market in only_recent:
            recents.append(only_recent[market])

        return recents

    def reorder(self, orders):
        markets = [x['market'] for x in orders]
        pending_cancel = True

        while pending_cancel:
            open_orders = self._bittrex.get_open_orders()

            if not open_orders:
                pending_cancel = False

            else:
                open_order_markets = [x['Exchange'] for x in open_orders]
                compare = [x for x in open_order_markets if x in markets]

                if len(compare) == 0:
                    pending_cancel = False

            if pending_cancel:
                sleep(1)

        placed = []
        expired = []

        for order in orders:
            market = order['market']
            quantity = order['quantity']

            recent_buy_order = self.get_buy_orders(market)
            market_summary = self._bittrex.get_market_summary(market)

            buy_price = recent_buy_order['market_price']
            current_price = market_summary['Last']
            current_gain = self._mathTime.variation(buy_price, current_price)

            selling = False

            if current_gain > self.minimum_gain_for_sell:
                selling = self._bittrex.sell_limit(market, quantity, current_price)

            add = {
                'market': market,
                'quantity': quantity,
                'price': current_price,
                'gain': current_gain}

            if selling:
                placed.append(add)
            else:
                expired.append(add)

        return {'placed': placed, 'expired': expired}
