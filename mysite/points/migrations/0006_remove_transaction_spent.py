# Generated by Django 4.0.1 on 2022-01-28 02:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0005_transaction_spent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='spent',
        ),
    ]
