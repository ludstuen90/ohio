# Generated by Django 2.1.7 on 2019-06-17 23:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('propertyrecords', '0025_auto_20190406_2317'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addressproperties',
            name='primary_address_line',
            field=models.CharField(blank=True, max_length=85),
        ),
        migrations.AlterField(
            model_name='addressproperties',
            name='secondary_address_line',
            field=models.CharField(blank=True, help_text='Apartment, Floor, Etc. ', max_length=85),
        ),
    ]
