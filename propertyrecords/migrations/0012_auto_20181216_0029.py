# Generated by Django 2.1.3 on 2018-12-16 00:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('propertyrecords', '0011_auto_20181216_0017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='legal_description',
            field=models.CharField(blank=True, max_length=250),
        ),
    ]
