# Generated by Django 5.1.3 on 2024-12-22 23:08

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0005_location_address_location_latitude_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='availability',
            name='day',
        ),
        migrations.AddField(
            model_name='availability',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='location',
            name='address',
            field=models.TextField(),
        ),
    ]
