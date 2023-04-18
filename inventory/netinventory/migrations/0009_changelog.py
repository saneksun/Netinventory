# Generated by Django 3.2.11 on 2022-05-02 23:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('netinventory', '0008_scanlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChangeLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField()),
                ('hostname', models.TextField()),
                ('serial_number', models.TextField(unique=True)),
                ('log', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
