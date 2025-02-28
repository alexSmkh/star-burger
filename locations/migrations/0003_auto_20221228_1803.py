# Generated by Django 3.2.15 on 2022-12-28 18:03

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0002_alter_location_updated_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='location',
            name='last_request_to_geocoder',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='дата запроса координат'),
            preserve_default=False,
        ),
    ]
