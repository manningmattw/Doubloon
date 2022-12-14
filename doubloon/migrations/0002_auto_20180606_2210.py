# Generated by Django 2.0.6 on 2018-06-07 03:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doubloon', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='currencies',
            options={'verbose_name': 'Currency', 'verbose_name_plural': 'Currencies'},
        ),
        migrations.AlterModelOptions(
            name='currentvalues',
            options={'verbose_name': 'Current Value', 'verbose_name_plural': 'Current Values'},
        ),
        migrations.AlterModelOptions(
            name='logs',
            options={'verbose_name': 'Log', 'verbose_name_plural': 'Logs'},
        ),
        migrations.AlterModelOptions(
            name='patternpriority',
            options={'verbose_name': 'Pattern Priority', 'verbose_name_plural': 'Pattern Priorities'},
        ),
        migrations.AlterModelOptions(
            name='purchasehistory',
            options={'verbose_name': 'Purchase History', 'verbose_name_plural': 'Purchase Histories'},
        ),
        migrations.AlterModelOptions(
            name='settings',
            options={'verbose_name': 'Setting', 'verbose_name_plural': 'Settings'},
        ),
        migrations.AlterModelOptions(
            name='statistics',
            options={'verbose_name': 'Statistics', 'verbose_name_plural': 'Statistics'},
        ),
        migrations.AlterModelOptions(
            name='trendmodel',
            options={'verbose_name': 'Trend Model', 'verbose_name_plural': 'Trend Models'},
        ),
        migrations.AlterModelOptions(
            name='wallet',
            options={'verbose_name': 'Wallet', 'verbose_name_plural': 'Wallets'},
        ),
        migrations.RenameField(
            model_name='currentvalues',
            old_name='minutes_elaped',
            new_name='minutes_elapsed',
        ),
        migrations.AlterField(
            model_name='trendmodel',
            name='deprecation',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='trendmodel',
            name='enable_down',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='trendmodel',
            name='enable_gutter',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='trendmodel',
            name='stagnation',
            field=models.BooleanField(default=True),
        ),
    ]
