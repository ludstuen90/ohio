# Generated by Django 2.1.5 on 2019-02-02 22:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('propertyrecords', '0018_auto_20190202_1340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='tax_delinquent_year',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
