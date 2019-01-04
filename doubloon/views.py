from django.shortcuts import render
from django.views import View
from .models import Settings
from .models import TradeMetrics
from .models import Orders
from .models import ForcedSell
from .models import LastAnalysis
from .library import math_time
from .library import bittrex


class Index(View):
    def __init__(self):
        self._bittrex = bittrex.BittrexAPI()
        self._mathTime = math_time.MathTime()

        self.base_currency = str(Settings.objects.get(setting='base_currency').value)
        self.bases = eval(Settings.objects.get(setting='safety_currencies').value)
        self.max_active_trades = int(Settings.objects.get(setting='max_active_trades').value)
        self.max_trade_allowed = float(Settings.objects.get(setting='max_trade_allowed').value)
        self.min_trade_allowed = float(Settings.objects.get(setting='min_trade_allowed').value)

        self.current_base_price = 0
        self.base_pending = 0.0

        metric_name = str(Settings.objects.filter(setting='trade_metric')[0].value)
        trade_metric = TradeMetrics.objects.filter(name=metric_name)[0]
        self.minimum_gain = float(trade_metric.minimum_gain_for_sell)

        market_summary = self._bittrex.get_market_summary('USD-' + self.base_currency)

        if market_summary:
            self.current_base_price = market_summary['Last']

    def _get_open_orders(self):
        open_orders = self._bittrex.get_open_orders()

        if not open_orders:
            return None

        for order in open_orders:
            price = order['Limit']
            quantity = order['Quantity']

            self.base_pending += price * quantity * .9975

        orders_pending = [x for x in open_orders if not x['CancelInitiated']]

        return orders_pending

    def _catalog_orders(self):
        orders_after = Orders.objects.filter(closed=None)

        if len(orders_after) > 0:
            orders_after = orders_after.earliest('opened').opened

        else:
            orders_after = Orders.objects.latest('closed').closed

        order_history = self._bittrex.get_order_history()

        if not order_history:
            return False

        buy_orders = []
        sell_orders = []

        for order in order_history:
            market = order['Exchange']
            timestamp = self._mathTime.dt_bittrex(order['Closed'])

            add = {
                'market': market,
                'base_currency': market.split('-')[0],
                'base_cost': order['Price'] + order['Commission'],
                'market_currency': market.split('-')[1],
                'market_quantity': order['Quantity'],
                'market_buy_price': order['Limit'],
                'closed': timestamp}

            add_to_buy = all([
                'buy' in order['OrderType'].lower(),
                timestamp >= orders_after,
                add['base_currency'] == self.base_currency])

            add_to_sell = all([
                'sell' in order['OrderType'].lower(),
                timestamp >= orders_after,
                add['base_currency'] == self.base_currency])

            if add_to_buy:
                buy_orders.append(add)
            elif add_to_sell:
                sell_orders.append(add)

        buy_orders = sorted(buy_orders, key=lambda k: (k['closed']))
        sell_orders = sorted(sell_orders, key=lambda k: (k['closed']))

        for order in buy_orders:
            order['opened'] = order['closed']
            order['closed'] = None

            stored_order = Orders.objects.filter(market=order['market'])
            stored_order = stored_order.filter(base_cost=order['base_cost'])
            stored_order = stored_order.filter(opened=order['opened'])

            recent = []
            most_recent_sell = None
            most_recent_time = 0

            for sold in sell_orders:
                conditions = [
                    order['market_quantity'] == sold['market_quantity'],
                    sold['closed'],
                    sold['market_buy_price'],
                    sold['base_cost'],
                    order['market'] == sold['market']]

                if all(conditions):
                    time_passed = (sold['closed'] - order['opened']).total_seconds()

                    if time_passed > 0:
                        recent.append({'time_passed': time_passed, 'sell': sold})

            for prospect in recent:
                if (not most_recent_sell) or (most_recent_time > prospect['time_passed']):
                    most_recent_sell = prospect['sell']
                    most_recent_time = prospect['time_passed']

            if most_recent_sell:
                order['closed'] = most_recent_sell['closed']
                order['market_sell_price'] = most_recent_sell['market_buy_price']
                order['base_earned'] = most_recent_sell['base_cost'] - order['base_cost']
                order['gain_loss'] = order['base_earned'] / order['base_cost']

            if stored_order.count() == 0:
                stored_order = Orders(**order)
                stored_order.save()

            elif stored_order.count() == 1:
                stored_order = stored_order[0]

                if not stored_order.closed and most_recent_sell:
                    stored_order.market_sell_price = order['market_sell_price']
                    stored_order.gain_loss = order['gain_loss']
                    stored_order.base_earned = order['base_earned']
                    stored_order.closed = order['closed']
                    stored_order.save()

        return True

    def _get_buy_orders(self, market=None):
        order_history = self._bittrex.get_order_history(market)

        if not order_history:
            return None

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

    def _wallet(self):
        balances = self._bittrex.get_balances()
        wallet = []

        for balance in balances:
            amount = balance['Available']
            currency = balance['Currency']
            add = {
                'balance': amount,
                'currency': currency}

            market = None

            if currency not in self.bases:
                if self.base_currency == 'BTC':
                    market = balance['BitcoinMarket']['MarketName']

                if self.base_currency == 'ETH':
                    market = balance['EthereumMarket']['MarketName']

            elif currency == self.base_currency:
                if balance['FiatMarket']:
                    market = balance['FiatMarket']['MarketName']

            add['market'] = market
            add['img'] = 'img/currencies/{}.png'.format(currency)
            add['balance_str'] = '%.8f' % amount

            wallet.append(add)

        wallet = sorted(wallet, key=lambda k: (k['balance']), reverse=True)

        return wallet

    def _wealth_and_price(self):
        safety = self.base_pending * self.current_base_price
        base = self.base_pending

        wealth = {'currencies': []}
        price = []

        for item in self.wallet:
            currency = item['currency']
            balance = item['balance']
            market = item['market']

            if currency in self.bases and currency != self.base_currency:
                safety += balance

                wealth['safety_currency'] = currency
                wealth['safety'] = '%.2f' % safety
                wealth['safety_img'] = 'img/currencies/{}.png'.format(currency)

            elif currency == self.base_currency:
                base += balance
                safety += self.current_base_price * balance

                price.append({
                    'currency': currency,
                    'price': '%.8f' % self.current_base_price,
                    'img': 'img/currencies/{}.png'.format(currency)})

                wealth['base_currency'] = currency
                wealth['base'] = '%.8f' % base
                wealth['base_img'] = 'img/currencies/{}.png'.format(currency)

            else:
                is_negative = False
                gain = 'N/A'

                recent_buy_order = self._get_buy_orders(market)
                orderbook = self._bittrex.get_best_from_orderbook(market, 'buy')

                buy_price = recent_buy_order['market_price']
                base_buy_price = recent_buy_order['base_price']
                offer_price = orderbook['Rate']
                current_gain = self._mathTime.variation(buy_price, offer_price)

                met_goal = current_gain >= self.minimum_gain
                goal = (1 + self.minimum_gain) * buy_price

                base += base_buy_price
                safety += self.current_base_price * base_buy_price

                if recent_buy_order:
                    if current_gain <= 0.005:
                        is_negative = True
                        gain = current_gain * -1

                    gain = ('%.2f' % (current_gain * 100)) + '%'

                price.append({
                    'currency': currency,
                    'price': '%.8f' % offer_price,
                    'img': 'img/currencies/{}.png'.format(currency)})

                wealth['currencies'].append({
                    'currency': currency,
                    'img': 'img/currencies/{}.png'.format(currency),
                    'gain_is_negative': is_negative,
                    'gain': gain,
                    'met_goal': met_goal,
                    'goal': '%.8f' % goal})

        return {'wealth': wealth, 'price': price}

    def _diversify_trade(self):
        wallets = [x for x in self.wallet if x['market']]
        wallets = [x for x in wallets if self.base_currency == x['market'].split('-')[0]]

        available = next(iter([x['balance'] for x in self.wallet if x['currency'] == self.base_currency]), 0)
        active = 0
        count = 0

        for wallet in wallets:
            recent_buy_order = self._get_buy_orders(wallet['market'])
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

    def _closed_orders(self):
        self._catalog_orders()

        db_orders = Orders.objects.exclude(closed=None).values()

        orders = []

        for order in db_orders:
            order['is_negative'] = order['gain_loss'] <= .005
            order['base_img'] = 'img/currencies/{}.png'.format(order['base_currency'])
            order['market_img'] = 'img/currencies/{}.png'.format(order['market_currency'])
            order['base_profit'] = '%.8f' % (order['base_earned'] + order['base_cost'])
            order['base_cost'] = '%.8f' % order['base_cost']
            order['base_earned'] = '%.8f' % order['base_earned']
            order['market_quantity'] = '%.8f' % order['market_quantity']
            order['market_buy_price'] = '%.8f' % order['market_buy_price']
            order['market_sell_price'] = '%.8f' % order['market_sell_price']
            order['gain_loss'] = '%.2f' % (order['gain_loss'] * 100)

            orders.append(order)

        orders = sorted(orders, key=lambda k: (k['closed']), reverse=True)

        return orders

    def _last_250_analyized(self):
        db_analyses = reversed(LastAnalysis.objects.all().order_by('-id')[:250])
        analyses = []

        for analysis in db_analyses:
            market_currency = analysis.market.split('-')[-1]
            try:
                reasons = eval(analysis.reasons)
            except Exception:
                reasons = []

            add = {
                'market_img': 'img/currencies/{}.png'.format(market_currency),
                'market': analysis.market,
                'rating': analysis.rating,
                'score': analysis.score,
                'reasons': reasons,
                'timestamp': analysis.timestamp}

            analyses.append(add)

        if len(analyses) == 0:
            return analyses

        analyses = sorted(analyses, key=lambda k: (k['timestamp']), reverse=True)

        return analyses

    def _current_crypto(self, open_orders):
        db_orders = Orders.objects.filter(closed=None).values()

        orders = []
        pending = []

        if open_orders:
            pending = [x['Exchange'].split('-')[-1] for x in open_orders]

        for order in db_orders:
            order['base_img'] = 'img/currencies/{}.png'.format(order['base_currency'])
            order['market_img'] = 'img/currencies/{}.png'.format(order['market_currency'])
            order['base_cost'] = '%.8f' % order['base_cost']
            order['market_quantity'] = '%.8f' % order['market_quantity']
            order['market_buy_price'] = '%.8f' % order['market_buy_price']
            order['is_pending'] = order['market_currency'] in pending

            orders.append(order)

        if len(orders) == 0:
            return orders

        orders = sorted(orders, key=lambda k: (k['opened']), reverse=True)

        return orders

    def _build_view(self, request):
        open_orders = self._get_open_orders()
        self.wallet = self._wallet()
        wealth_and_price = self._wealth_and_price()
        closed_orders = self._closed_orders()
        current_crypto = self._current_crypto(open_orders)
        analyses = self._last_250_analyized()
        diversify = self._diversify_trade()
        available = diversify['available']
        allowed = diversify['allowed']

        cancel_buttons = []

        if open_orders and len(current_crypto) > 0:
            for order in open_orders:
                currency = order['Exchange'].split('-')[-1]
                uuid = order['OrderUuid']

                cancel_buttons.append({'currency': currency, 'uuid': uuid})

        trade_actions = any([
            len(current_crypto) > 0,
            len(cancel_buttons) > 0])

        context = {
            'last_refresh': self._mathTime.now_refresh(),
            'wallet': self.wallet,
            'available': available,
            'allowed': allowed,
            'wealth': wealth_and_price['wealth'],
            'price': wealth_and_price['price'],
            'closed_orders': closed_orders,
            'analyses': analyses,
            'current_crypto': current_crypto,
            'trade_actions': trade_actions,
            'cancel_buttons': cancel_buttons}

        return context

    def handle_post(self, request):
        if 'buy_currency' in request.POST:
            market = request.POST['market']
            amount = request.POST['amount']
            price = request.POST['price']
            price_custom = request.POST['price_actual']

            try:
                amount = float(amount)
            except Exception:
                amount = None

            current_price = None

            if price == 'bid':
                orderbook = self._bittrex.get_best_from_orderbook(market, 'buy')
                current_price = orderbook['Rate'] if orderbook else None
            if price == 'ask':
                orderbook = self._bittrex.get_best_from_orderbook(market, 'sell')
                current_price = orderbook['Rate'] if orderbook else None
            if price == 'custom':
                try:
                    current_price = float(price_custom)
                except Exception:
                    current_price = None

            if current_price and amount:
                quantity = float('%.8f' % ((amount * .9975) / current_price))

                self._bittrex.buy_limit(market, quantity, current_price)

        if 'force_sell' in request.POST:
            market = request.POST['market']

            recent_buy_order = self._get_buy_orders(market)
            orderbook = self._bittrex.get_best_from_orderbook(market, 'buy')
            offer_price = orderbook['Rate']
            quantity = recent_buy_order['quantity']

            uuid = self._bittrex.sell_limit(market, quantity, offer_price)

            if uuid:
                db_data, created = ForcedSell.objects.get_or_create(uuid=uuid)

                if created:
                    db_data.market = market
                    db_data.save()

        if 'cancel_order' in request.POST:
            uuid = request.POST['uuid']
            self._bittrex.cancel_order(uuid)

    def get(self, request):
        template = 'index.html'
        context = self._build_view(request)

        return render(request, template, context)

    def post(self, request):
        template = 'index.html'

        self.handle_post(request)
        context = self._build_view(request)

        return render(request, template, context)
