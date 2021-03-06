import csv
import datetime
import os
import re
from _decimal import InvalidOperation

import pytz
import scrapy

from ohio import settings
from propertyrecords import models, utils
from bs4 import BeautifulSoup


HEADERS = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, "
                          "like Gecko) Chrome/70.0.3538.102 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "X-MicrosoftAjax": "Delta=true"
            }

HEADERS.update(settings.CONTACT_INFO_HEADINGS)


class WarrenSpider(scrapy.Spider):
    name = 'cuyahoga'
    allowed_domains = ['myplace.cuyahogacounty.us']

    def retrieve_all_warren_county_urls(self):
        self.cuyahoga_county_object, created = models.County.objects.get_or_create(name="Cuyahoga")

        scrape_apts_and_hotels_from_list = True
        # Excludes any properties that have been scraped before... in this way, we can scrape faster
        # If setting Rescrape to True, will need to alter this code to look at different last_scraped_by dates;
        # as of now, the code just looks for last_scraped as blank
        rescrape = False

        if scrape_apts_and_hotels_from_list:
            list_of_parcel_ids = []
            script_dir = os.path.dirname(__file__)  # <-- absolute dir this current script is in
            rel_path = "../scraper_data_drops/cuyahogareal.csv"  # <-- Look two directories up for relevant CSV files
            abs_file_path = os.path.join(script_dir, rel_path)

            with open(abs_file_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for number, row in enumerate(reader):
                    list_of_parcel_ids.append(row['PARCEL_ID'])

            # Ensure we have a property record for all items
            for property in list_of_parcel_ids:
                property, created = models.Property.objects.get_or_create(parcel_number=property,
                                                                          county=self.cuyahoga_county_object)
            all_cuyahoga_properties = models.Property.objects.filter(county=self.cuyahoga_county_object,
                                                                          parcel_number__in=list_of_parcel_ids
                                                                          ).order_by('?')
        else:
            all_cuyahoga_properties = models.Property.objects.filter(county=self.cuyahoga_county_object,
                                                                     )
        # If we are not running a rescrape, take out properties that have already been scraped
        if rescrape is False:
            all_cuyahoga_properties = all_cuyahoga_properties.filter(last_scraped_one__isnull=True)

        for property in all_cuyahoga_properties:
            prop_dict = {
                'url': f'''https://myplace.cuyahogacounty.us/{utils.convert_string_to_base64_bytes_object(property.parcel_number)}?city={utils.convert_string_to_base64_bytes_object('99')}&searchBy={utils.convert_string_to_base64_bytes_object('Parcel')}&dataRequested={utils.convert_string_to_base64_bytes_object('General Information')}''',
                'parcel_number': property.parcel_number,
            }
            yield prop_dict

    def __init__(self):
        self.logged_out = False

    def start_requests(self):
       # Ensure we have a county in the database
        self.warren_county_object, created = models.County.objects.get_or_create(name="Cuyahoga")

        # We want to assign headers for each request triggered. Override the request object
        # sent over to include Lucia's contact information
        for parameter_dictionary in self.retrieve_all_warren_county_urls():
            yield scrapy.Request(parameter_dictionary['url'], dont_filter=True,
                          headers=HEADERS,
                          meta={'parcel_number': parameter_dictionary['parcel_number']
                            },
                          )

    def parse(self, response):
        """
        This method is responsible for downloading information for Cuyahoga
        records from the myplace.cuyahogacounty.us site.
        :param response:
        :return:
        """

        parcel_number = response.meta['parcel_number']
        property = models.Property.objects.get(parcel_number=parcel_number)

        # GENERAL PAGE
        property.school_district_name = response.xpath('/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[2]/div[2]/text()').extract_first()
        property.tax_district = response.xpath("/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[1]/div[4]/text()").extract_first()
        try:
            property.land_use = utils.parse_ohio_state_use_code(response.xpath("/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[3]/div[2]/text()").extract_first())
        except ValueError:
            property.land_user = response.xpath("/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[3]/div[2]/text()").extract_first()
        property.legal_description = response.xpath("//div[@class='generalInfoValue col-lg-3']/text()").extract_first()[:249]
        property.primary_owner = response.xpath("/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[1]/ul[1]/li[2]/text()").extract_first().strip()
        property.property_rating = response.xpath("/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[2]/div[4]/text()").extract_first()
        property.save()

        # TAX BILL PAGE
        yield scrapy.Request(
            url=f'''https://myplace.cuyahogacounty.us/{utils.convert_string_to_base64_bytes_object(property.parcel_number)}?city={utils.convert_string_to_base64_bytes_object('99')}&searchBy={utils.convert_string_to_base64_bytes_object('Parcel')}&dataRequested={utils.convert_string_to_base64_bytes_object('Tax Bill')}''',
            method='GET',
            callback=self.parse_tax_page_information,
            meta={'parcel_number': response.meta['parcel_number']},
            dont_filter=True,
            headers=HEADERS
        )

        yield scrapy.Request(
            url=f'''https://myplace.cuyahogacounty.us/{utils.convert_string_to_base64_bytes_object(
                property.parcel_number)}?city={utils.convert_string_to_base64_bytes_object(
                '99')}&searchBy={utils.convert_string_to_base64_bytes_object(
                'Parcel')}&dataRequested={utils.convert_string_to_base64_bytes_object('Land')}''',
            method='GET',
            callback=self.parse_land_information,
            meta={'parcel_number': response.meta['parcel_number']},
            dont_filter=True,
            headers=HEADERS
        )

        yield scrapy.Request(
            url=f'''https://myplace.cuyahogacounty.us/{utils.convert_string_to_base64_bytes_object(
                property.parcel_number)}?city={utils.convert_string_to_base64_bytes_object(
                '99')}&searchBy={utils.convert_string_to_base64_bytes_object(
                'Parcel')}&dataRequested={utils.convert_string_to_base64_bytes_object('Transfers')}''',
            method='GET',
            callback=self.parse_transfer_information,
            meta={'parcel_number': response.meta['parcel_number']},
            dont_filter=True,
            headers=HEADERS

        )

        # SCHOOL DISTRICT: (* Requires VPN access)
        #https://thefinder.tax.ohio.gov/StreamlineSalesTaxWeb/default_SchoolDistrict.aspx
        # school_district

        # TAX INFO (* Requires VPN access)
        # Ideally would look by address, but zip code could provide a starting point. (zip + 4 digits would be ideal)

    def parse_tax_page_information(self, response):
        """

        :param request:
        :return:
        """

        parcel_number = response.meta['parcel_number']
        soup = BeautifulSoup(response.body, 'html.parser')

        our_property = models.Property.objects.get(parcel_number=parcel_number)

        our_property.property_class = response.xpath("/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[1]/div[1]/div[1]/div[5]/div[2]/text()").extract_first()
        our_property.owner_occupancy_indicated = utils.convert_y_n_to_boolean(response.xpath("//div[@class='taxDataBody']/div[1]/div[1]/div[3]/table/tr[2]/td[2]/text()").extract_first())

        tax_year = response.xpath("//div[@class='HeaderHighlight']/text()").extract_first().split(' ')[0]

        tax_values_object, created = models.TaxData.objects.get_or_create(property_record=our_property,
                                                                          tax_year=tax_year)
        delq_balance = soup.find("table", {"class": "ChargeAndPaymentDetailTable"}).find(text=re.compile('DELQ BALANCE'))
        year = soup.find( "div", {"class":"HeaderHighlight"}).getText()[0:4]

        if delq_balance == 'DELQ BALANCE':
            our_property.tax_delinquent = True
            our_property.tax_delinquent_year = int(year)

        try:
            tax_values_object.market_value = utils.convert_taxable_value_string_to_integer(soup.body.find(text=re.compile('Market Values')).parent.parent.parent.findAll('tr')[3].findAll('td')[1].contents[0])
            tax_values_object.taxable_value = utils.convert_taxable_value_string_to_integer(soup.body.find(text=re.compile('Assessed Values')).parent.parent.parent.findAll('tr')[3].findAll('td')[1].contents[0])
            tax_values_object.taxes_paid = utils.convert_taxable_value_string_to_integer(response.xpath("//div[@class='row']//div[3]//div[2]//b[1]/text()").extract()[0])
        except InvalidOperation:
            pass
        tax_values_object.save()

        property_address, created = models.PropertyAddress.objects.get_or_create(property = our_property)
        property_address_dict = utils.cuyahoga_addr_splitter(response.xpath("//div[@class='TaxBillSummaryHeadingTable']//div[2]//div[2]/text()").extract_first())
        property_address.primary_address_line = property_address_dict['primary_address']
        property_address.city = property_address_dict['city']
        property_address.state = property_address_dict['state']
        property_address.zipcode = property_address_dict['zipcode']
        property_address.save()

        tax_addr = response.xpath("//div[@class='TaxBillSummaryHeadingTable']//div[3]//div[2]/text()").extract_first()

        parsed_tax_result = utils.cuyahoga_tax_address_parser(tax_addr)

        tax_object, created = models.TaxAddress.objects.get_or_create(name=parsed_tax_result['primary_address_line'])
        tax_object.primary_address_line = parsed_tax_result['secondary_address_line']
        tax_object.city = parsed_tax_result['city']
        tax_object.state = parsed_tax_result['state']
        tax_object.zipcode = parsed_tax_result['zipcode']
        tax_object.save()

        our_property.tax_address = tax_object
        our_property.owner = response.xpath("/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[1]/div[1]/div[1]/div[1]/div[2]/text()").extract_first()
        our_property.save()

    def parse_land_information(self, response):
        parcel_number = response.meta['parcel_number']

        property_object = models.Property.objects.get(parcel_number=parcel_number)

        property_object.legal_acres = response.xpath("/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[2]/div[4]/div[4]/text()").extract_first()
        property_object.save()


    def parse_transfer_information(self, response):
        parcel_number = response.meta['parcel_number']
        property_object = models.Property.objects.get(parcel_number=parcel_number)

        # Delete existing property transfer records so that we can be sure our database reflects information
        # on the site.
        models.PropertyTransfer.objects.filter(property=property_object).delete()

        # COUNT NUMBER OF TRANSFERS WE WILL WANT TO RETURN
        total_number_of_transfers = response.xpath(
            'count(/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div)').extract_first()
        transfer_as_digit = total_number_of_transfers.split('.')
        digit_to_add = (int(transfer_as_digit[0]) + 1)

        for transfer_item in range(1, digit_to_add):

            date = response.xpath(
                f'''/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[{transfer_item}]/div[1]/div[1]/span[2]/text()''').extract_first()

            guarantor_guarantee = response.xpath(
                f'''/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[{transfer_item}]/table/tr/td/text()''').extract()

            try:
                guarantor = guarantor_guarantee[1]
            except IndexError:
                guarantor = ''
            try:
                guarantee = guarantor_guarantee[0]
            except IndexError:
                guarantee = ''

            sale_amount = response.xpath(f'''/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[{transfer_item}]/div[2]/div[1]/table[1]/tbody[1]/tr[1]/td[4]/text()''').extract_first()

            conveyance_amount = response.xpath(f'''/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[{transfer_item}]/div[2]/div[1]/table[1]/tbody[1]/tr[1]/td[5]/text()''').extract_first()
            conveyance_number_string = response.xpath(
                f'''/html[1]/body[1]/div[1]/div[3]/div[2]/div[1]/div[1]/div[4]/div[2]/div[1]/div[{transfer_item}]/div[2]/div[1]/table[1]/tbody[1]/tr[1]/td[6]/text()''').extract_first().strip(' ')
            try:
                conveyance_number = int(conveyance_number_string)
            except ValueError:
                conveyance_number = ''
            print("PROP NUMBER: ", property_object)
            property_transfer_obj, created = models.PropertyTransfer.objects.get_or_create(
                property=property_object,
                transfer_date=utils.datetime_to_date_string_parser(date, '%m/%d/%Y'),
                sale_amount=utils.convert_taxable_value_string_to_integer(sale_amount),
                guarantor=guarantor,
                guarantee=guarantee,
                conveyance_fee=utils.convert_taxable_value_string_to_integer(conveyance_amount),
                conveyance_number=conveyance_number
            )
            property_transfer_obj.save()
            property_object.last_scraped_one = datetime.datetime.now(pytz.utc)
            property_object.save()
