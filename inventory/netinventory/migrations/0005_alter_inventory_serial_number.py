# Generated by Django 3.2.11 on 2022-01-28 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netinventory', '0004_nodes_snmpcommunity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='serial_number',
            field=models.TextField(unique=True),
        ),
    ]
