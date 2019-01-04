# -*- coding: UTF-8 -*-

from django.core.management.base import BaseCommand
from doubloon.library import bittrex
from doubloon.library import math_time
from doubloon.library import marketplace
from doubloon.models import Settings
from doubloon.models import TradeMetrics
from doubloon.models import LastAnalysis
from doubloon.models import Ranks
from pathlib import Path
import os
import sys


class Command(BaseCommand):
    help = 'Runs a trade cycle'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._bittrex = bittrex.BittrexAPI()
        self._mathtime = math_time.MathTime()
        self._marketplace = marketplace.Marketplace()

        self.buying = eval(Settings.objects.get(setting='buying').value)
        self.ignore_markets = eval(Settings.objects.get(setting='ignore_markets').value)
        self.selling = eval(Settings.objects.get(setting='selling').value)
        self.max_active_trades = int(Settings.objects.get(setting='max_active_trades').value)
        self.max_trade_allowed = float(Settings.objects.get(setting='max_trade_allowed').value)
        self.min_trade_allowed = float(Settings.objects.get(setting='min_trade_allowed').value)
        metric_name = str(Settings.objects.get(setting='trade_metric').value)

        trade_metric = TradeMetrics.objects.get(name=metric_name)
        self.long_sma_period = int(trade_metric.long_sma_period)
        self.short_sma_period = int(trade_metric.short_sma_period)
        self.ema_period = int(trade_metric.ema_period)
        self.tick_interval = str(trade_metric.tick_interval)
        self.total_top_markets = int(trade_metric.total_top_markets)
        self.minimum_gain_for_sell = float(trade_metric.minimum_gain_for_sell)
        self.ranks = list(Ranks.objects.filter(name__in=eval(trade_metric.ranks)))

        self.lockfile = 'doubloon_lock'

    def create_lock(self):
        if Path(self.lockfile).exists():
            lockfile = open(self.lockfile, 'r')

            lockdatetime = int(self._mathtime.unformat_time(lockfile.read()))
            now = int(self._mathtime.now())

            if now - lockdatetime > 1200:
                self.remove_lock()
            else:
                sys.exit(1)

        now = self._mathtime.format_time(self._mathtime.now())
        lockfile = open(self.lockfile, 'w')
        lockfile.write(now)
        lockfile.close()

        return True

    def remove_lock(self):
        try:
            os.remove(self.lockfile)
        except OSError:
            pass

        return True

    def sell_process(self):
        wallets = [x for x in self._marketplace.wallets if x['market']]

        for wallet in wallets:
            print('Checking if ready to sell', wallet['symbol'], 'in market', wallet['market'] + '\n')
            selling = self.sell_if_ready(wallet['market'])

            if selling:
                print('\nSell order placed for %.8f' % selling['price'], '(Gain %.3f' % (selling['gain'] * 100) + '%)')
            else:
                print('\n' + wallet['symbol'] + ' is not ready to be sold')

            print('')

        return False

    def sell_if_ready(self, market):
        recent_buy_order = self._marketplace.get_buy_orders(market)
        orderbook = self._bittrex.get_best_from_orderbook(market, 'buy')

        if not all([recent_buy_order, orderbook]):
            return False

        quantity = recent_buy_order['quantity']
        buy_price = recent_buy_order['market_price']
        buy_price_base = recent_buy_order['base_price']
        offer_price = orderbook['Rate']
        offer_quantity = orderbook['Quantity']
        offer_price_base = offer_price * quantity * .9975
        current_gain = self._mathtime.variation(buy_price, offer_price)
        minimum_sell_price = (1 + self.minimum_gain_for_sell) * buy_price
        minimum_sell_base = minimum_sell_price * quantity * .9975

        print('    Buy Price:                   %.8f' % buy_price)
        print('    Current Best Offer:          %.8f' % offer_price)
        print('    Minimum Offer Price:         %.8f' % minimum_sell_price)
        print('    Increase/Decrease:           %.2f' % (current_gain * 100) + '%')
        print('    Quantity:                    %.8f' % quantity)
        print('    Current Offer Quantity:      %.8f' % offer_quantity)
        print('    Buy Price (' + self._marketplace.base_currency + '):             %.8f' % buy_price_base)
        print('    Current Best Offer (' + self._marketplace.base_currency + '):    %.8f' % offer_price_base)
        print('    Minimum Offer Price (' + self._marketplace.base_currency + '):   %.8f' % minimum_sell_base)

        if current_gain < self.minimum_gain_for_sell:
            return False

        if offer_quantity < quantity:
            return False

        candles = self._bittrex.get_candles(market, self.tick_interval)
        candles = self._mathtime.heikin_ashi_candles(candles)
        candles = self._mathtime.expand_candles(
            base_candles=candles,
            long_sma_period=self.long_sma_period,
            short_sma_period=self.short_sma_period,
            ema_period=self.ema_period)

        ema = candles[-1]['ema']
        short_sma = candles[-1]['short_sma']

        stagnant_price = sum([x['close'] for x in candles[-3:]]) / 3 == candles[-1]['close']

        conditions = any([
            ema <= short_sma,
            stagnant_price,
            len([x for x in candles[-2:] if self._mathtime.is_doji(x)]) > 0,
            len([x for x in candles[-2:] if self._mathtime.is_shooting_star(x)]) > 0,
            len([x for x in candles[-2:] if self._mathtime.is_bearish(x)]) > 0,
            len([x for x in candles[-2:] if x['close'] <= x['open']]) == 2])

        if conditions:
            selling = self._bittrex.sell_limit(market, quantity, offer_price)

            if selling:
                return {'price': offer_price, 'gain': current_gain}

        return False

    def buy_process(self):
        diversity = self._marketplace.diversify()

        allowed = diversity['allowed']
        available = diversity['available']

        if allowed == 0:
            print('No more currencies are allowed to be purchased at this time')

            return None

        if available == 0:
            print('No funds are available for buying currencies at this time')

            return None

        print('Allowed to buy up to {} currencies using {} {} for each'.format(
            allowed,
            '%.8f' % available,
            self._marketplace.base_currency))

        print('\nLooking for best currency to buy')
        markets = self.find_market()

        if len(markets) == 0:
            print('  No currencies are worth investing in at this time')

            return None

        if len(markets) > allowed:
            markets = markets[(-1 * (allowed - 1)):]

        for market in markets:
            buying = self._marketplace.buy_limit(market, available, log=True)

            if buying:
                print('\nBuy order placed for %.8f' % buying['quantity'], 'at %.8f' % buying['price'])
            else:
                print('\nUnable to place order in market {}'.format(market))

        return None

    def fifty_day_avg_volume(self, market):
        candles = self._bittrex.get_candles(market, 'day')

        if not candles:
            return 0

        if len(candles) > 50:
            candles = candles[-50:]

        candles = [x['volume'] for x in candles]

        avg_volume = self._mathtime.average(candles)

        return avg_volume

    def high_trade_activity(self, market):
        market_history = self._bittrex.get_market_history(market)

        if not market_history:
            return False

        recent_history = [x for x in market_history if x['recent']]

        minutes_between_trades = self._mathtime.minutes(
            market_history[-4]['timestamp'],
            market_history[-1]['timestamp']) / 3.0

        high_trade = all([
            len(recent_history) >= 100,
            minutes_between_trades < 2])

        return high_trade

    def top_markets(self):
        ignore = [x['symbol'] for x in self._marketplace.wallets]
        markets = self._bittrex.get_market_summaries()
        markets = [x for x in markets if x['MarketName'].split('-')[0] == self._marketplace.base_currency]
        markets = [x for x in markets if x['MarketName'].split('-')[1] not in ignore]

        before = len(markets)

        print('  Sorting top {} markets and removing any that are too risky'.format(before))
        top_markets = []

        for market in markets:
            price_spread = self._mathtime.variation(market['Bid'], market['Ask'])

            add = {
                'name': market['MarketName'],
                'gain_loss': self._mathtime.variation(market['PrevDay'], market['Last']),
                'price_spread': price_spread}

            if price_spread < 0.003:
                top_markets.append(add)

        top_markets = sorted(top_markets, key=lambda k: (k['price_spread']), reverse=True)
        top_markets = sorted(top_markets, key=lambda k: (k['gain_loss']))

        after = before - len(top_markets)

        print('  Removed {} markets with a crazy price spread'.format(after))

        markets = top_markets[(self.total_top_markets * -1):]
        top_markets = []

        print('  Using top {} markets and eliminating any without high trade activity'.format(len(markets)))

        for market in markets:
            high_trade_activity = self.high_trade_activity(market['name'])

            if high_trade_activity:
                market['avg_volume'] = self.fifty_day_avg_volume(market['name'])
                top_markets.append(market)

        top_markets = sorted(top_markets, key=lambda k: (k['price_spread']), reverse=True)
        top_markets = sorted(top_markets, key=lambda k: (k['avg_volume'], k['gain_loss']))

        return top_markets

    def market_data_points(self, market):
        true_candles = self._bittrex.get_candles(market['name'], self.tick_interval)
        all_candles = self._mathtime.heikin_ashi_candles(true_candles)
        all_candles = self._mathtime.expand_candles(
            base_candles=all_candles,
            long_sma_period=self.long_sma_period,
            short_sma_period=self.short_sma_period,
            ema_period=self.ema_period)

        candles = all_candles[-10:]
        ema = candles[-1]['ema']
        long_sma = candles[-1]['long_sma']
        short_sma = candles[-1]['short_sma']
        avg_volume = market['avg_volume']
        volume = candles[-1]['volume']
        ema_variance = self._mathtime.variation(candles[-2]['ema'], ema)
        sma_variance = self._mathtime.variation(candles[-2]['short_sma'], short_sma)
        long_sma_variance = self._mathtime.variation(candles[-2]['long_sma'], long_sma) * 100
        spread = self._mathtime.variation(long_sma, ema)
        dojis = len([x for x in candles[-3:] if self._mathtime.is_doji(x)])
        hammers = len([x for x in candles[-3:] if self._mathtime.is_hammer(x)])
        vol_gt_avgvol = len([x for x in candles[-3:] if x['volume'] > avg_volume])
        c_gt_o = len([x for x in candles if x['close'] > x['open']])
        c_gt_o3 = len([x for x in candles[-3:] if x['close'] > x['open']])
        trend = self._mathtime.variation(candles[0]['close'], candles[-1]['close'])
        minutes_since_last_goal = self._mathtime.minutes_since_last_goal(true_candles)
        decimal_points = self._mathtime.decimal_points(true_candles[-1]['close'])
        last_cross = self._mathtime.last_cross(all_candles, 'ema', 'long_sma')

        data_points = {
            'candles': candles,
            'ema': ema,
            'long_sma': long_sma,
            'short_sma': short_sma,
            'avg_volume': avg_volume,
            'volume': volume,
            'ema_variance': ema_variance,
            'sma_variance': sma_variance,
            'long_sma_variance': long_sma_variance,
            'spread': spread,
            'dojis': dojis,
            'hammers': hammers,
            'vol_gt_avgvol': vol_gt_avgvol,
            'c_gt_o': c_gt_o,
            'c_gt_o3': c_gt_o3,
            'trend': trend,
            'minutes_since_last_goal': minutes_since_last_goal,
            'decimal_points': decimal_points,
            'last_cross': last_cross}

        return data_points

    def build_positions(self, data_points):
        positions = []

        for rank in self.ranks:
            label = rank.label
            score = rank.score
            match_list = eval(rank.match_list)

            match = []
            for matchstr in match_list:
                this_match = []

                for word in matchstr.split(' '):
                    if word in data_points:
                        word = data_points[word]

                    this_match.append(str(word))

                this_match = ' '.join(this_match)

                match.append(eval(this_match))

            positions.append({
                'label': label,
                'score': score,
                'match': match})

        return positions

    def find_market(self):
        print('  Finding top', self._marketplace.base_currency, 'markets to review')

        top_markets = self.top_markets()
        top_markets = [m for m in top_markets if m['name'] not in self.ignore_markets]

        print('  Analyzing the positions of', len(top_markets), 'potentially worthy markets')

        best_markets = []
        all_markets = []

        for market in top_markets:
            data_points = self.market_data_points(market)
            positions = self.build_positions(data_points)

            good_positions = [x for x in positions if all(x['match'])]

            if len(good_positions) >= 1:
                position = sorted(good_positions, key=lambda k: (k['score']))[0]

                score = position['score'] - data_points['spread']
                rating = position['rating']

                print('     Scored %.1f' % score + ' for ' + market['name'] + ' - ' + rating)

                best_markets.append({'market': market['name'], 'score': score, 'rating': rating})
                all_markets.append({'market': market['name'], 'score': score, 'rating': rating})
            else:
                reasons = []

                if data_points['ema_variance'] <= -0.5:
                    reasons.append('EMA VARIANCE: ' + str(data_points['ema_variance']) + ' <= 0')
                if data_points['long_sma_variance'] < -0.02:
                    reasons.append('LONG SMA VARIANCE: ' + str(data_points['long_sma_variance']) + ' < -0.02')
                if data_points['long_sma_variance'] > .05:
                    reasons.append('LONG SMA VARIANCE: ' + str(data_points['long_sma_variance']) + ' > .05')
                if data_points['last_cross'] > 60:
                    reasons.append('LAST CROSS: ' + str(data_points['last_cross']) + ' > 30')
                if data_points['ema'] >= data_points['long_sma']:
                    reasons.append('EMA >= LONG SMA: ' + str(data_points['ema']) + ' > ' + str(data_points['long_sma']))
                if data_points['trend'] <= 0:
                    reasons.append('TREND: ' + str(data_points['trend']) + ' <= 0')
                if data_points['volume'] <= 0:
                    reasons.append('VOLUME: ' + str(data_points['volume']) + ' <= 0')
                if data_points['c_gt_o'] <= 3:
                    reasons.append('NOT ENOUGH GAINS: ' + str(data_points['c_gt_o']) + ' <= 3')
                if data_points['decimal_points'] >= 6:
                    reasons.append('CURRENCY WORTHLESS: ' + str(data_points['decimal_points']) + ' >= 6')
                if data_points['minutes_since_last_goal'] >= 1440:
                    reasons.append('GOAL NOT MET RECENTLY: ' + str(data_points['minutes_since_last_goal']) + ' >= 1440')

                all_markets.append({'market': market['name'], 'score': 0, 'rating': 'Bad', 'reasons': reasons})

        if len(all_markets) > 0:
            all_markets = sorted(all_markets, key=lambda k: (k['score']))

            for add in all_markets:
                add = LastAnalysis(**add)
                add.save()

        if len(best_markets) == 0:
            return best_markets

        best_markets = sorted(best_markets, key=lambda k: (k['score']))
        best_markets = list(set([x['market'] for x in best_markets]))

        return best_markets

    def trade(self):
        skip_selling = self._marketplace.skip_selling

        print('Available Balances\n')
        for wallet in self._marketplace.wallets:
            print('    %.8f' % wallet['balance'] + ' ' + wallet['symbol'])

        print('\nReviewing for open orders')
        open_orders = self._marketplace.check_for_open_orders()

        pending = open_orders['pending']
        cancelled = open_orders['cancelled']
        reorders = open_orders['reorder']

        if len(cancelled) > 0:
            for order in cancelled:
                print('  Cancelled order in market', order['Exchange'], 'for', order['Quantity'], 'at', order['Limit'])

        if len(pending) > 0:
            for order in pending:
                print('  Open order is pending in market', order['Exchange'],
                      'for', order['Quantity'], 'at', order['Limit'])

        if len(reorders) > 0:
            orders = self._marketplace.reorder(reorders)

            placed = orders['placed']
            expired = orders['expired']

            for order in placed:
                print('  Resubmitted order in', order['market'], 'for', order['quantity'], 'at', order['price'])

            for order in expired:
                print('  Previous order in', order['market'], 'for', order['quantity'],
                      'at', order['price'], 'has missed its opportunity and has been cancelled.')

        if (len(cancelled) > 0) or (len(pending) > 0) or (len(reorders) > 0):
            print('  Trading for new currency disabled until all orders complete')
            return None
        else:
            print('  No open orders detected')

        print('')

        if self.selling and not skip_selling:
            self.sell_process()

        if self.buying:
            self.buy_process()

        return None

    def handle(self, *args, **options):
        self.create_lock()

        now = self._mathtime.format_time(self._mathtime.now())
        print('\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(' Starting Trade Cycle at', now)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n')

        self.trade()

        now = self._mathtime.format_time(self._mathtime.now())
        print('\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(' Trade Cycle completed at', now)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n')

        self.remove_lock()
