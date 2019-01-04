# -*- coding: UTF-8 -*-

from django.core.management.base import BaseCommand
from doubloon.library import bittrex
from doubloon.library import math_time
from sklearn import preprocessing, cross_validation, svm
from sklearn.linear_model import LinearRegression
import datetime
import pandas as pd
import numpy as np


class Command(BaseCommand):
    help = 'Runs a trade cycle'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._bittrex = bittrex.BittrexAPI()
        self._mathtime = math_time.MathTime()

    def test(self):
        df = self._bittrex.get_candles('BTC-ETH', 'oneMin', as_dataframe=True)
        df = df[['close']]

        forecast_out = int(30)
        df['predition'] = df[['close']].shift(-forecast_out)

        print(df.head())

    def handle(self, *args, **options):
        now = self._mathtime.format_time(self._mathtime.now())
        print('\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(' Starting Test at', now)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n')

        self.test()

        now = self._mathtime.format_time(self._mathtime.now())
        print('\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(' Test completed at', now)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n')
