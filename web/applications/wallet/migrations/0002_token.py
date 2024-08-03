# Generated by Django 5.0.6 on 2024-07-25 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Дата изменения')),
                ('status', models.CharField(choices=[('draft', 'Черновик'), ('published', 'Опубликовано')], default='published', max_length=50, verbose_name='Статус')),
                ('mint_account', models.CharField(max_length=100, unique=True, verbose_name='Mint account (address)')),
                ('token_account', models.CharField(blank=True, max_length=100, verbose_name='Token account (address)')),
                ('program', models.CharField(blank=True, max_length=100, verbose_name='Token program id')),
                ('decimals', models.PositiveSmallIntegerField(default=9, verbose_name='Token decimals')),
                ('state', models.CharField(blank=True, max_length=100, verbose_name='Token state')),
                ('symbol', models.CharField(blank=True, max_length=10, verbose_name='Token symbol')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='Token name')),
                ('description', models.CharField(blank=True, max_length=1000, verbose_name='Token description')),
                ('metadata_uri', models.CharField(blank=True, max_length=2000, verbose_name='Token metadata uri')),
                ('metadata_account', models.CharField(blank=True, max_length=100, verbose_name='Metadata account (address)')),
                ('raw_metadata', models.JSONField(blank=True, default=dict, null=True, verbose_name='Raw token metadata')),
                ('mint_authority', models.CharField(blank=True, max_length=100, verbose_name='Mint authority (address)')),
                ('freeze_authority', models.CharField(blank=True, max_length=100, verbose_name='Freeze authority (address)')),
            ],
            options={
                'verbose_name': 'token',
                'verbose_name_plural': 'tokens',
            },
        ),
    ]