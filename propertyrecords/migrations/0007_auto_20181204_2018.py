# Generated by Django 2.1.3 on 2018-12-04 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('propertyrecords', '0006_auto_20181202_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='date_sold',
            field=models.DateField(blank=True, help_text='Date a property transfer was recorded. Might not have actually meant property sold for money, in the case of inheriting a property. ', null=True),
        ),
    ]