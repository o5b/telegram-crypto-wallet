# Generated by Django 5.0.6 on 2024-07-30 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='telegram_language',
            field=models.CharField(blank=True, max_length=16),
        ),
    ]
