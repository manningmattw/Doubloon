# Generated by Django 2.0.6 on 2018-12-15 00:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doubloon', '0007_auto_20180722_1435'),
    ]

    operations = [
        migrations.CreateModel(
            name='LastAnalysis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('market', models.CharField(max_length=100)),
                ('rating', models.CharField(max_length=100)),
                ('score', models.IntegerField()),
            ],
            options={
                'verbose_name_plural': 'Last Analyses',
                'verbose_name': 'Last Analysis',
            },
        ),
    ]
