import csv

from django.core.management.base import BaseCommand
import os

from propertyrecords import models


class Command(BaseCommand):
    help = 'Command for querying parcel IDs'

    def handle(self, *args, **options):
        warren_county, created = models.County.objects.get_or_create(name='Warren')
        script_dir = os.path.dirname(__file__)  # <-- absolute dir this current script is in
        rel_path = "../../parcel_data/warren.csv" # <-- Look two directores up for relevant CSV files
        abs_file_path = os.path.join(script_dir, rel_path)
        print("Warren initial loading process initiated.")
        with open(abs_file_path, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for number, row in enumerate(reader):
                warren_county_property_item, created = models.Property.objects.get_or_create(parcel_number=row['Parcel Number'])
                warren_county_property_item.account_number = row['Account Number']
                warren_county_property_item.county = warren_county
                if row['Account Number']:
                    warren_county_property_item.save()

                if number % 1000 == 0:
                    print('We have processed the following number of reecords: ', number)

        print("Warren initial loading process completed.")

