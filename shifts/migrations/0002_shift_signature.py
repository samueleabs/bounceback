# Generated by Django 5.1.3 on 2024-12-14 04:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='signature',
            field=models.TextField(blank=True, null=True),
        ),
    ]
