from django.db.models import Model
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import IntegerField
from django.db.models import FloatField
from django.db.models import TextField


class Settings(Model):
    setting = CharField(max_length=256)
    value = TextField()

    def __str__(self):
        return self.setting

    class Meta:
        verbose_name = 'Setting'
        verbose_name_plural = 'Settings'


class TradeMetrics(Model):
    name = CharField(max_length=128)
    tick_interval = CharField(max_length=32)
    long_sma_period = IntegerField()
    short_sma_period = IntegerField()
    ema_period = IntegerField()
    total_top_markets = IntegerField()
    minimum_gain_for_sell = FloatField()
    ranks = TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Trade Metric'
        verbose_name_plural = 'Trade Metrics'


class Orders(Model):
    market = CharField(max_length=100)
    base_currency = CharField(max_length=100)
    base_cost = FloatField()
    base_earned = FloatField(default=None, null=True, blank=True)
    market_currency = CharField(max_length=100)
    market_quantity = FloatField()
    market_buy_price = FloatField()
    market_sell_price = FloatField(default=None, null=True, blank=True)
    gain_loss = FloatField(default=None, null=True, blank=True)
    opened = DateTimeField(auto_now=False, auto_now_add=False)
    closed = DateTimeField(auto_now=False, auto_now_add=False, default=None, null=True, blank=True)

    def __str__(self):
        return self.market

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'


class ForcedSell(Model):
    market = CharField(max_length=100)
    uuid = CharField(max_length=400)

    def __str__(self):
        return self.market + '::' + self.uuid

    class Meta:
        verbose_name = 'Forced Sell'
        verbose_name_plural = 'Forced Sells'


class LastAnalysis(Model):
    timestamp = DateTimeField(auto_now=True)
    market = CharField(max_length=100)
    rating = CharField(max_length=100)
    score = IntegerField()
    reasons = TextField()

    def __str__(self):
        return self.market + ' - ' + self.rating

    class Meta:
        verbose_name = 'Last Analysis'
        verbose_name_plural = 'Last Analyses'


class Ranks(Model):
    name = CharField(max_length=100)
    label = CharField(max_length=100)
    score = IntegerField()
    match_list = TextField()

    def __str__(self):
        return self.label + ' (' + str(self.score) + ')'

    class Meta:
        verbose_name = 'Rank'
        verbose_name_plural = 'Ranks'
