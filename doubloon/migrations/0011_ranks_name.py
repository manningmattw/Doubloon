# Generated by Django 2.0.6 on 2018-12-21 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doubloon', '0010_auto_20181221_1235'),
    ]

    operations = [
        migrations.AddField(
            model_name='ranks',
            name='name',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
