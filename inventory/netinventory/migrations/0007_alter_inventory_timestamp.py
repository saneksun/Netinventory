# Generated by Django 3.2.11 on 2022-02-02 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netinventory', '0006_inventory_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='timestamp',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
