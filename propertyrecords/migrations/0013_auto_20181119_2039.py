# Generated by Django 2.1.3 on 2018-11-19 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('propertyrecords', '0012_auto_20181119_2036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='land_use',
            field=models.IntegerField(),
        ),
    ]