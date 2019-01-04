#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from doubloon.backend.library import trading
from threading import Thread


class Doubloons(object):
    def __init__(self):
        self.trading_module = trading.Trading()

    def daemon(self):
        trading_thread = Thread(target=self.trading)
        trading_thread.start()

    def trading(self):
        self.trading_module.sequencer()


if __name__ == "__main__":
    doubloons = Doubloons()
    doubloons.daemon()
