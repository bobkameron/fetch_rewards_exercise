# Generated by Django 4.0.1 on 2022-01-27 23:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payer',
            old_name='company',
            new_name='name',
        ),
    ]
