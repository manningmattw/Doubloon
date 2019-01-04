#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import time
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
import pytz


class MathTime(object):
    def now(self):
        return time.strftime('%Y%m%d%H%M%S')

    def now_refresh(self):
        return time.strftime('%b %d, %Y  %H:%M:%S')

    def dt_bittrex(self, timestamp):
        if timestamp[-5] != '+':
            timestamp += '+0000'

        if '.' in timestamp:
            return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z')

        return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')

    def bittrex_dt(self, date_time):
        tz = pytz.timezone('America/Chicago')

        return datetime.strftime('%Y-%m-%dT%H:%M:%S.%f', make_aware(date_time, tz))

    def snapshot(self, start=None, weeks=0, days=0, hours=0, minutes=0, seconds=0):
        if not start:
            start = self.now()

        start = datetime(
            int(time.strftime('%Y', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%m', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%d', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%H', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%M', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%S', time.strptime(start, '%Y%m%d%H%M%S'))))

        end = datetime.strftime(start - timedelta(
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds), '%Y%m%d%H%M%S')

        return end

    def bittrex_to_doubloons(self, timestamp):
        if '.' not in timestamp:
            return time.strftime('%Y%m%d%H%M%S', time.strptime(timestamp, '%Y-%m-%dT%H:%M:%S'))

        return time.strftime('%Y%m%d%H%M%S', time.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f'))

    def bittrex_compare_times(self, new, old):
        return time.strptime(new, '%Y-%m-%dT%H:%M:%S.%f') > time.strptime(old, '%Y-%m-%dT%H:%M:%S.%f')

    def doubloon_compare_times(self, new, old):
        return time.strptime(new, '%Y%m%d%H%M%S') > time.strptime(old, '%Y%m%d%H%M%S')

    def utc_to_local(self, timestamp):
        hour = int(time.strftime('%H', time.strptime(timestamp, '%Y%m%d%H%M%S')))
        change = int(time.strftime('%z').replace('0', '').replace('+', ''))

        hour += change

        if hour < 0:
            hour = 24 + hour
        if hour > 23:
            hour = hour - 24

        hour = str(hour)

        if len(hour) == 1:
            hour = '0' + hour

        local = time.strftime('%Y%m%d', time.strptime(timestamp, '%Y%m%d%H%M%S'))
        local += hour
        local += time.strftime('%M%S', time.strptime(timestamp, '%Y%m%d%H%M%S'))

        return local

    def seconds(self, start, end=None):
        if not end:
            end = self.now()

        start = datetime(
            int(time.strftime('%Y', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%m', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%d', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%H', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%M', time.strptime(start, '%Y%m%d%H%M%S'))),
            int(time.strftime('%S', time.strptime(start, '%Y%m%d%H%M%S'))))

        end = datetime(
            int(time.strftime('%Y', time.strptime(end, '%Y%m%d%H%M%S'))),
            int(time.strftime('%m', time.strptime(end, '%Y%m%d%H%M%S'))),
            int(time.strftime('%d', time.strptime(end, '%Y%m%d%H%M%S'))),
            int(time.strftime('%H', time.strptime(end, '%Y%m%d%H%M%S'))),
            int(time.strftime('%M', time.strptime(end, '%Y%m%d%H%M%S'))),
            int(time.strftime('%S', time.strptime(end, '%Y%m%d%H%M%S'))))

        seconds = (end - start).total_seconds()

        return seconds

    def minutes(self, start, end=None):
        seconds = self.seconds(start, end)

        return round(seconds / 60)

    def forward(self, start=None, days=0, hours=0, minutes=0, seconds=0):
        if start:
            start = datetime(
                int(time.strftime('%Y', time.strptime(start, '%Y%m%d%H%M%S'))),
                int(time.strftime('%m', time.strptime(start, '%Y%m%d%H%M%S'))),
                int(time.strftime('%d', time.strptime(start, '%Y%m%d%H%M%S'))),
                int(time.strftime('%H', time.strptime(start, '%Y%m%d%H%M%S'))),
                int(time.strftime('%M', time.strptime(start, '%Y%m%d%H%M%S'))),
                int(time.strftime('%S', time.strptime(start, '%Y%m%d%H%M%S'))))
        else:
            start = datetime.now()

        end = datetime.strftime(start + timedelta(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds), '%Y%m%d%H%M%S')

        return end

    def format_time(self, timestamp):
        timestamp = time.strptime(str(timestamp), '%Y%m%d%H%M%S')

        return time.strftime('%m/%d/%Y %H:%M:%S', timestamp)

    def unformat_time(self, timestamp):
        timestamp = time.strptime(str(timestamp), '%m/%d/%Y %H:%M:%S')

        return time.strftime('%Y%m%d%H%M%S', timestamp)

    def variation(self, oldest, newest):
        if not oldest:
            return 0.0

        return (float(newest) - float(oldest)) / float(oldest)

    def value(self, quantity, price):
        return float(quantity) * float(price)

    def average(self, values):
        return float(sum(values)) / float(len(values))

    def sma(self, candles, length):
        # simple moving average

        sma = []
        average = []

        for candle in candles:
            close = candle['close']

            average.append(close)

            while len(average) > length:
                average.pop(0)

            if len(average) == length:
                sma.append(self.average(average))

        if sma == []:
            sma = [1, 0]

        return sma

    def ema(self, candles, length):
        # exponential moving average

        sma = self.sma(candles, length)

        if sma == [1, 0]:
            return sma

        ema = [sma[0]]
        multiplier = 2 / (length + 1)

        i = 0

        for candle in candles:
            close = candle['close']
            new = ((close - ema[i]) * multiplier) + ema[i]

            ema.append(new)

            i += 1

        return ema

    def vma(self, candles, length):
        # volume moving average

        vma = []
        average = []

        for candle in candles:
            close = candle['volume']

            average.append(close)

            while len(average) > length:
                average.pop(0)

            if len(average) == length:
                vma.append(self.average(average))

        if vma == []:
            vma = [1, 0]

        return vma

    def volume_trend(self, candles, length):
        trend = length / 2
        starting_trend = trend
        volumes = [x['volume'] for x in candles[(-1 * length):]]
        signal = 'stalled'
        strong = False
        weak = False

        i = 0

        while i <= len(volumes) - 1:
            if i > 0:
                if volumes[i] > volumes[i - 1]:
                    trend += 1
                elif volumes[i] < volumes[i - 1]:
                    trend -= 1

            i += 1

        if trend > starting_trend:
            signal = 'good'
            strong = (length - trend) > (trend - starting_trend)
            weak = (length - trend) < (trend - starting_trend)

        if trend < starting_trend:
            signal = 'bad'
            strong = (starting_trend - trend) > trend
            weak = (starting_trend - trend) < trend

        return {'signal': signal, 'strong': strong, 'weak': weak}

    def last_cross(self, candles, field1, field2):
        candles = list(reversed(candles))

        current_field1 = candles[0][field1]
        current_field2 = candles[0][field2]

        if current_field1 == current_field2:
            return 0

        looking_for = 'above'
        if current_field1 > current_field2:
            looking_for = 'below'

        met = False
        passed = 1
        total_candles = len(candles) - 1

        while (passed <= total_candles) and (not met):
            this_field1 = candles[passed][field1]
            this_field2 = candles[passed][field2]

            conditions = [
                this_field1 >= this_field2 and looking_for == 'above',
                this_field1 <= this_field2 and looking_for == 'below']

            if any(conditions):
                met = True

            else:
                passed += 1

        if not met:
            return 99999999

        return passed

    def expand_candles(self, base_candles, long_sma_period, short_sma_period, ema_period):
        candles = []
        i = 0

        while i <= len(base_candles) - 1:
            candle = base_candles[i]
            ls = i + 1 - long_sma_period
            ss = i + 1 - short_sma_period
            e = i + 1 - ema_period

            if i >= long_sma_period - 1:
                long_sma = self.average([x['close'] for x in base_candles[ls:i]])
                short_sma = self.average([x['close'] for x in base_candles[ss:i]])
                ema = self.average([x['close'] for x in base_candles[e:i]])

                if candle['close'] <= candle['open']:
                    candle['volume'] = candle['volume'] * -1

                candle['long_sma'] = long_sma
                candle['short_sma'] = short_sma
                candle['ema'] = ema

                candles.append(candle)

            i += 1

        return candles

    def slope(self, candles):
        average = []

        for candle in candles:
            close = candle['close']

            average.append(close)

        run = len(average)

        if run >= 6:
            start = sum([average[0], average[1], average[2]]) / 3.0
            end = sum([average[-1], average[-2], average[-3]]) / 3.0
            rise = end - start
            slope = rise / run

            return slope

        return -1.0

    def candle_color(self, candle):
        if candle['open'] >= candle['close']:
            return "red"

        if candle['close'] > candle['open']:
            return "green"

        return None

    def candle_size(self, candle):
        color = self.candle_color(candle)

        if color == "red":
            return candle['open'] - candle['close']

        if color == "green":
            return candle['close'] - candle['open']

        return 0

    def top_wick(self, candle):
        color = self.candle_color(candle)

        if color == "red":
            return candle['high'] - candle['open']

        if color == "green":
            return candle['high'] - candle['close']

        return 0

    def bottom_wick(self, candle):
        color = self.candle_color(candle)

        if color == "red":
            return candle['close'] - candle['low']

        if color == "green":
            return candle['open'] - candle['low']

        return 0

    def pattern(self, one, two):
        color1 = self.candle_color(one)
        color2 = self.candle_color(two)

        variation = self.variation(one['close'], two['close'])
        pattern = "none"
        direction = "neutral"

        one['bwick'] = self.bottom_wick(one)
        one['twick'] = self.top_wick(one)
        two['bwick'] = self.bottom_wick(two)
        two['twick'] = self.top_wick(two)

        if variation > 0:
            direction = "up"
        elif variation < 0:
            direction = "down"

        if (color1 == "red") and (color2 == "green"):
            pattern = "bullish engulfing"
            direction = "up"

        if (color1 == "red") and (one['bwick'] > one['twick']) and (one['close'] != one['open']):
            pattern = "hammer"
            direction = "up"

        if (color1 == "green") and (color2 == "red"):
            if (two['close'] > one['open']) and (two['open'] < one['close']):
                pattern = "bearish engulfing"
                variation = self.variation(two['close'], one['close'])
                direction = "down"

            if (one['close'] <= two['open']):
                pattern = "dark cloud cover"
                direction = "down"

            if (color2 == "red") and (one['bwick'] < one['twick']) and (one['close'] != one['open']):
                pattern = "shooting star"
                direction = "down"

        if one['close'] == one['open']:
            variation = self.variation(one['close'], two['close'])

            if color2 == "green":
                pattern = "doji"
                direction = "up"

            if color2 == "red":
                pattern = "doji"
                direction = "down"

            if ((one['close'] == one['low']) and (one['close'] == one['high'])) or (variation == 0):
                pattern = 'stagnant'
                direction = 'neutral'

        return {'pattern': pattern, 'direction': direction, 'variation': variation}

    def is_doji(self, candle):
        conditions = [
            candle['open'] == candle['close'],
            candle['high'] > candle['close'],
            candle['low'] < candle['open']]

        return all(conditions)

    def is_hammer(self, candle):
        op = candle['open']
        cl = candle['close']
        hi = candle['high']
        lo = candle['low']

        condition1 = all([
            cl > op,
            hi == cl,
            op - lo >= (cl - op) * 2])

        condition2 = all([
            op > cl,
            hi == op,
            cl - lo >= (op - cl) * 2])

        return any([condition1, condition2])

    def is_shooting_star(self, candle):
        op = candle['open']
        cl = candle['close']
        hi = candle['high']
        lo = candle['low']

        condition1 = all([
            cl > op,
            lo == op,
            hi - cl >= (cl - op) * 2])

        condition2 = all([
            op > cl,
            lo == cl,
            hi - cl >= (op - cl) * 2])

        return any([condition1, condition2])

    def is_bearish(self, candle):
        op = candle['open']
        cl = candle['close']
        hi = candle['high']
        lo = candle['low']

        condition1 = all([
            cl > op,
            hi - cl > (op - lo) * 4])

        condition2 = all([
            op > cl,
            hi - op >= (cl - lo) * 2])

        return any([condition1, condition2])

    def heikin_ashi_candles(self, candles):
        ha_candles = []
        last_candle = None

        for candle in candles:
            if last_candle:
                this_open = candle['open']
                this_high = candle['high']
                this_low = candle['low']
                this_close = candle['close']
                last_open = last_candle['open']
                last_close = last_candle['close']

                ha_candle = {
                    'close': (this_open + this_high + this_low + this_close) / 4.0,
                    'open': (last_open + last_close) / 2.0,
                    'high': max(this_high, this_open, this_close),
                    'low': min(this_low, this_open, this_close),
                    'volume': candle['volume'],
                    'base_volume': candle['base_volume'],
                    'timestamp': candle['timestamp']}

                ha_candles.append(ha_candle)

            last_candle = candle

        return ha_candles

    def minutes_since_last_goal(self, candles):
        candles = list(reversed(candles))

        current_price = candles[0]['close']
        minimum_sell_price = (1 + self.minimum_gain_for_sell) * current_price

        met = False
        minutes = 1
        candle_minutes = len(candles) - 1

        while (minutes <= candle_minutes) and (not met):
            price = candles[minutes]['close']

            if price >= minimum_sell_price:
                met = True

            else:
                minutes += 1

        if minutes >= candle_minutes:
            return 99999999

        return minutes

    def decimal_points(self, price):
        price = '%.8f' % price
        points = 0

        if price.split('.')[1] == '00000000':
            return 0

        for i in price.split('.')[1]:
            points += 1

            if int(i) != 0:
                return points

        return points

    def increase(self, price):
        return price + 0.00000001

    def decrease(self, price):
        return price - 0.00000001
