# Generated by Django 2.0.6 on 2018-06-06 02:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Currencies',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.TextField()),
                ('name', models.TextField()),
                ('trading', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='CurrentValues',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('initial', models.FloatField()),
                ('gutter', models.FloatField()),
                ('break_even', models.FloatField()),
                ('deprecated', models.FloatField()),
                ('optimal', models.FloatField()),
                ('current', models.FloatField()),
                ('minutes_elaped', models.IntegerField()),
                ('gutter_ticks', models.IntegerField()),
                ('down_ticks', models.IntegerField()),
                ('last_close', models.FloatField()),
                ('timestamp', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Logs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.CharField(max_length=64)),
                ('message', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='PatternPriority',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pattern', models.CharField(max_length=255)),
                ('priority', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PurchaseHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=64)),
                ('buy_timestamp', models.CharField(max_length=64)),
                ('sell_timestamp', models.CharField(max_length=64)),
                ('buy_value', models.FloatField()),
                ('sell_value', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('setting', models.TextField()),
                ('value', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Statistics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('optimal', models.IntegerField()),
                ('up', models.IntegerField()),
                ('deprecated', models.IntegerField()),
                ('break_even', models.IntegerField()),
                ('down', models.IntegerField()),
                ('gutter', models.IntegerField()),
                ('user_forced', models.IntegerField()),
                ('limit_reached', models.IntegerField()),
                ('predicted_loss', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='TrendModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('safety_symbol', models.CharField(max_length=64)),
                ('tx_fee', models.FloatField()),
                ('tick_interval', models.CharField(max_length=64)),
                ('optimal_gaim', models.FloatField()),
                ('enable_gutter', models.CharField(max_length=64)),
                ('gutter', models.FloatField()),
                ('max_gutter_ticks', models.IntegerField()),
                ('enable_down', models.CharField(max_length=64)),
                ('max_down_ticks', models.IntegerField()),
                ('deprecation', models.CharField(max_length=64)),
                ('deprecation_rate', models.FloatField()),
                ('stagnation', models.CharField(max_length=64)),
                ('stagnation_minutes', models.FloatField()),
                ('sma_length', models.IntegerField()),
                ('ema_length', models.IntegerField()),
                ('last_cross_threshold', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=64)),
                ('buy_price', models.CharField(max_length=64)),
                ('quantity', models.CharField(max_length=64)),
                ('timestamp', models.CharField(max_length=64)),
            ],
        ),
    ]