# -*- coding: UTF-8 -*-

from django.core.management.base import BaseCommand
from doubloon.models import LastAnalysis


class Command(BaseCommand):
    help = 'Processes reasons why currencies were not bought'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **kwargs):
        analyses = list(LastAnalysis.objects.exclude(reasons=[]))

        reasons = {}
        solo_reasons = {}
        samples = {}
        affinity = {}
        last_cross = []
        ema_variance = []
        count = 0

        for analysis in analyses:
            try:
                reason_list = eval(analysis.reasons)
                market = analysis.market

                if market not in affinity:
                    affinity[market] = 0

                affinity[market] += 1

                for reason in reason_list:
                    subject = reason.split(':')[0]
                    sample = reason.split(': ')[1]

                    if subject not in reasons:
                        reasons[subject] = 0
                        samples[subject] = sample

                    if len(reason_list) == 1 and subject not in solo_reasons:
                        solo_reasons[subject] = 0

                    if len(reason_list) == 1:
                        solo_reasons[subject] += 1

                        if subject == 'LAST CROSS':
                            last_cross.append(sample)

                        if subject == 'EMA VARIANCE':
                            ema_variance.append(sample)

                    reasons[subject] += 1

                count += 1

            except Exception:
                pass

        print('Total Analyzed Results: {}'.format(count))

        print('\nAffinity:')
        affinity = sorted(affinity.items(), reverse=True, key=lambda x: x[1])[:50]

        i = 0
        line = ''
        for item in affinity:
            market = item[0]
            count = item[1]
            spaces = (12 - len(market)) * ' '
            line += '  {}{}{}'.format(market, spaces, count)

            if i < 2:
                line += ' ' * 10
                i += 1
            else:
                print(line)
                line = ''
                i = 0

        print('\nTotal Count for Each Reason:')
        for reason in reasons:
            spaces = (30 - len(reason)) * ' '
            print('  {}{}{}'.format(reason, spaces, reasons[reason]))

        print('\nCount of Each Reason Being the Only Reason:')
        for reason in solo_reasons:
            spaces = (30 - len(reason)) * ' '
            print('  {}{}{}'.format(reason, spaces, solo_reasons[reason]))

        print('\nSample Reason Data:')
        for reason in samples:
            spaces = (30 - len(reason)) * ' '
            print('  {}{}{}'.format(reason, spaces, samples[reason]))

        print('\nTime Since Last Cross Samples:')
        last_cross = [int(sample.split(' > ')[0]) for sample in last_cross]
        count = {}
        for last in last_cross:
            if last not in count:
                count[last] = 0
            count[last] += 1

        last_cross = sorted(list(set(last_cross)))

        highest_10 = last_cross[-10:]
        lowest_10 = last_cross[:10]
        average = sum(last_cross) / len(last_cross) if len(last_cross) > 0 else 0

        print('  Highest 10:', highest_10)
        print('  Lowest 10: ', lowest_10)
        print('  Average:   ', average)

        print('\nEMA Variance Samples:')
        ema_variance = [float(sample.split(' <= ')[0]) for sample in ema_variance]
        count = {}
        for last in ema_variance:
            if last not in count:
                count[last] = 0
            count[last] += 1

        ema_variance = sorted(list(set(ema_variance)))

        highest_10 = ema_variance[-10:]
        lowest_10 = ema_variance[:10]
        average = sum(ema_variance) / len(ema_variance) if len(ema_variance) > 0 else 0

        print('  Highest 10:', highest_10)
        print('  Lowest 10: ', lowest_10)
        print('  Average:   ', average)

        print('')
