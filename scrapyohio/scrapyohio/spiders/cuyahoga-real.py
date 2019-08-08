# -*- coding: utf-8 -*-
import csv
import datetime
import json
import os
import pickle
import sys

import scrapy
from scrapy import FormRequest, Request
from scrapy.exceptions import CloseSpider
from scrapy.utils.response import open_in_browser

from ohio import settings
from propertyrecords import models, utils
from bs4 import BeautifulSoup


HEADERS = {
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    'Accept-Encoding': "gzip, deflate, br",
    'Accept-Language': "es-AR,es;q=0.9,en-US;q=0.8,en;q=0.7,es-419;q=0.6",
    'Cache-Control': "max-age=0",
    'Connection': "keep-alive",
    'Content-Type': "application/x-www-form-urlencoded",
    'Host': "recorder.cuyahogacounty.us",
    'Origin': "https://recorder.cuyahogacounty.us",
    'Referer': "https://recorder.cuyahogacounty.us/searchs/parcelsearchs.aspx",
    'Upgrade-Insecure-Requests': "1",
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
    'cache-control': "no-cache",
            }

HEADERS.update(settings.CONTACT_INFO_HEADINGS)

payload = "__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwUKLTQ3NzIzMzE3NA9kFgICAw9kFgYCAQ8WAh4EVGV4dGVkAgMPPCsADQEMFCsABQUPMDowLDA6MSwwOjIsMDozFCsAAhYGHwAFBEhvbWUeBVZhbHVlBQExHgtOYXZpZ2F0ZVVybAUCfi9kFCsAAhYGHwAFD1NlYXJjaCBEYXRhYmFzZR8BBQEyHwIFHX4vc2VhcmNocy9nZW5lcmFsc2VhcmNocy5hc3B4FCsABAULMDowLDA6MSwwOjIUKwACFgYfAAUOR2VuZXJhbCBTZWFyY2gfAQUBMx8CBR1%2BL3NlYXJjaHMvZ2VuZXJhbHNlYXJjaHMuYXNweGQUKwACFgYfAAUNUGFyY2VsIFNlYXJjaB8BBQE0HwIFHH4vc2VhcmNocy9wYXJjZWxzZWFyY2hzLmFzcHhkFCsAAhYGHwAFFFZldGVyYW4gR3JhdmUgU2VhcmNoHwEFAjY2HwIFOmh0dHA6Ly9yZWNvcmRlci5jdXlhaG9nYWNvdW50eS51cy92ZXRlcmFuL0dyYXZlU2VhcmNoLmFzcHhkFCsAAhYGHwAFDlByb3BlcnR5IEFsZXJ0HwEFAjYxHwIFNH4vL01lbWJlcnMvTG9naW4uYXNweD9SZXR1cm5Vcmw9JTJmbWVtYmVycyUyZm5vdGlmaWMUKwACBQMwOjAUKwACFgYfAAUOUHJvcGVydHkgQWxlcnQfAQUCNjIfAgVkaHR0cDovL3JlY29yZGVyLmN1eWFob2dhY291bnR5LnVzL01lbWJlcnMvTG9naW4uYXNweD9SZXR1cm5Vcmw9JTJmbWVtYmVycyUyZm5vdGlmaWNhdGlvbm1hbmFnZXIuYXNweGQUKwACFgYfAAUNRmlzY2FsIE9mZmljZR8BBQI3Mh8CBSZodHRwOi8vZmlzY2Fsb2ZmaWNlci5jdXlhaG9nYWNvdW50eS51c2RkAg8PFgIfAAUZDQoJCTxjZW50ZXI%2BwqA8L2NlbnRlcj4NCmRkf9vKGL1V%2B%2FKL93FohlCdJQAAAAA%3D&__VIEWSTATEGENERATOR=B99DED13&__EVENTVALIDATION=%2FwEWBgKXtO2JDQLn5fPPBALa8JHqAgKS0KzHDQK72KCUAgLCqo%2BIBEh%2FUvTvj3m26LhHjPat6rAAAAAA&txtRecStart=12%2F4%2F1800&txtRecEnd=12%2F4%2F2018&ParcelID=00338375&lstQuery=1&ValidateButton=Begin%20Search&undefined="
form_data = {'__EVENTTARGET': '',
             '__EVENTARGUMENT': '',
             '__VIEWSTATE': '/wEPDwUKLTQ3NzIzMzE3NA9kFgICAw9kFgYCAQ8WAh4EVGV4dGVkAgMPPCsADQEMFCsABQUPMDowLDA6MSwwOjIsMDozFCsAAhYGHwAFBEhvbWUeBVZhbHVlBQExHgtOYXZpZ2F0ZVVybAUCfi9kFCsAAhYGHwAFD1NlYXJjaCBEYXRhYmFzZR8BBQEyHwIFHX4vc2VhcmNocy9nZW5lcmFsc2VhcmNocy5hc3B4FCsABAULMDowLDA6MSwwOjIUKwACFgYfAAUOR2VuZXJhbCBTZWFyY2gfAQUBMx8CBR1+L3NlYXJjaHMvZ2VuZXJhbHNlYXJjaHMuYXNweGQUKwACFgYfAAUNUGFyY2VsIFNlYXJjaB8BBQE0HwIFHH4vc2VhcmNocy9wYXJjZWxzZWFyY2hzLmFzcHhkFCsAAhYGHwAFFFZldGVyYW4gR3JhdmUgU2VhcmNoHwEFAjY2HwIFOmh0dHA6Ly9yZWNvcmRlci5jdXlhaG9nYWNvdW50eS51cy92ZXRlcmFuL0dyYXZlU2VhcmNoLmFzcHhkFCsAAhYGHwAFDlByb3BlcnR5IEFsZXJ0HwEFAjYxHwIFNH4vL01lbWJlcnMvTG9naW4uYXNweD9SZXR1cm5Vcmw9JTJmbWVtYmVycyUyZm5vdGlmaWMUKwACBQMwOjAUKwACFgYfAAUOUHJvcGVydHkgQWxlcnQfAQUCNjIfAgVkaHR0cDovL3JlY29yZGVyLmN1eWFob2dhY291bnR5LnVzL01lbWJlcnMvTG9naW4uYXNweD9SZXR1cm5Vcmw9JTJmbWVtYmVycyUyZm5vdGlmaWNhdGlvbm1hbmFnZXIuYXNweGQUKwACFgYfAAUNRmlzY2FsIE9mZmljZR8BBQI3Mh8CBSZodHRwOi8vZmlzY2Fsb2ZmaWNlci5jdXlhaG9nYWNvdW50eS51c2RkAg8PFgIfAAUZDQoJCTxjZW50ZXI+wqA8L2NlbnRlcj4NCmRkf9vKGL1V+/KL93FohlCdJQAAAAA=',
             '__VIEWSTATEGENERATOR': 'B99DED13',
             '__EVENTVALIDATION': '/wEWBgKXtO2JDQLn5fPPBALa8JHqAgKS0KzHDQK72KCUAgLCqo+IBEh/UvTvj3m26LhHjPat6rAAAAAA',
             'txtRecStart': '12/4/1800',
             'txtRecEnd': '12/4/2018',
             'lstQuery': '1',
             'ValidateButton': 'Begin Search',
    }

class WarrenSpider(scrapy.Spider):
    name = 'cuyahoga-real'
    allowed_domains = ['recorder.cuyahogacounty.us']

    def retrieve_all_warren_county_urls(self):

        scrape_apts_and_hotels_from_list = False
        continue_where_last_scrape_left_off = False
        seven_days_ago = datetime.datetime.today() - datetime.timedelta(days=7)

        self.cuyahoga_county_object, created = models.County.objects.get_or_create(name="Cuyahoga")

        if continue_where_last_scrape_left_off and scrape_apts_and_hotels_from_list:

            sys.exit("Both variables continue_where_last_scrape_left_off and scrape_apts_and_hotels_from_list cannot be"
                     "true at the same time.")

        if continue_where_last_scrape_left_off:
            self.all_cuyahoga_properties = models.Property.objects.filter(county=self.cuyahoga_county_object,
                                                                        ).exclude(
                                                                    last_scraped_one__gte=seven_days_ago
                                                                    ).order_by('?')

        elif scrape_apts_and_hotels_from_list:
            list_of_parcel_ids = []
            script_dir = os.path.dirname(__file__)  # <-- absolute dir this current script is in
            rel_path = "../scraper_data_drops/cuyahogareal.csv"  # <-- Look two directories up for relevant CSV files
            abs_file_path = os.path.join(script_dir, rel_path)
            with open(abs_file_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for number, row in enumerate(reader):
                    list_of_parcel_ids.append(row['PARCEL_ID'])



            self.all_cuyahoga_properties = models.Property.objects.filter(county=self.cuyahoga_county_object,
                                                                          parcel_number__in=list_of_parcel_ids
                                                                          ).order_by('?')
        else:
            self.all_cuyahoga_properties = models.Property.objects.filter(county=self.cuyahoga_county_object,
                                                                          id=121265,
                                                                          ).order_by('?')


        for item in self.all_cuyahoga_properties:
            yield {'url': "https://recorder.cuyahogacounty.us/searchs/parcelsearchs.aspx", 'parcel_id':
                item.parcel_number}

    def __init__(self, *args, **kwargs):
        self.logged_out = False

    def start_requests(self):
       # Ensure we have a county in the database
        self.warren_county_object, created = models.County.objects.get_or_create(name="Cuyahoga")

        # We want to assign headers for each request triggered. Override the request object
        # sent over to include Lucia's contact information
        for enumerator, package in enumerate(self.retrieve_all_warren_county_urls()):
            form_data['ParcelID'] = package['parcel_id']

            yield FormRequest(
                    url=package['url'],
                    formdata=form_data,
                    method='POST',
                    meta={'page': 1, 'parcel_id': package['parcel_id'], 'cookiejar': enumerator},
                    dont_filter=True,
                    headers=HEADERS,
            )


    def mortgage_processor(self, response):
            open_in_browser(response)

    def parse(self, response, *args, **kwargs):
        """

        :param response:
        :return:
        """
        if response.url == 'https://recorder.cuyahogacounty.us/LockedOut.aspx':
            # If we recive this page, it's because our IP address has been blocked!
            raise CloseSpider('ip_address_blocked')
        open_in_browser(response)
        print("RESPONSE URL: ", response.url)

        soup = BeautifulSoup(response.text, 'html.parser')
        property_object = models.Property.objects.get(parcel_number=response.meta['parcel_id'])
        primary_owner = property_object.owner
        deed_date = utils.parse_recorder_items(soup, primary_owner, 'DEED')
        property_object.last_scraped_one = datetime.datetime.now()
        # if deed_date:
        mortgage_date = utils.parse_recorder_items(soup, primary_owner, 'MORT')
        print("Searched: ", response.meta['parcel_id'], "we found mortgage date of: ", mortgage_date,
              " and deed date of ", deed_date)
        try:
            property_object.date_sold = datetime.datetime.strptime(deed_date, '%m/%d/%Y')
        except TypeError:
            # No Deed found
            pass
        try:
            property_object.date_of_mortgage = datetime.datetime.strptime(mortgage_date, '%m/%d/%Y')
        except TypeError:
            # No mortgage found
            pass

        # If mortgage found, try to get info on it
        if mortgage_date is not None:
            mortgage_form_data = {
                        '__EVENTARGUMENT:': 'Select$3',
                        '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$GridView1',
                        '__EVENTVALIDATION': '/wEWHwKRqcb2DALmiPuaDALxv6ehCgKhmtThAgLmiO/3BAKE96yhCgLqm9ThAgLmiNPADgK7sduhCgLjmdThAgLmiMe9BwLOqOGhCgLEmdThAgLmiIuOAQL1nt+hCgKlmdThAgLmiL/rCQKo1NShCgL+mNThAgLmiOP1AwKfkNKhCgLXmNThAgLmiJfRCALSg9ihCgK4mNThAgLmiJvwCQKzxML0CQLfmuicAgLmiI+tDgLGv8j0CQLAmuicAn4yKh9a8G32ieIkJ/fGhMQAAAAA',
                        '__VIEWSTATE': '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',
                         '__VIEWSTATEGENERATOR': '29B21770',
                        'ctl00$ContentPlaceHolder1$GridView1$ctl05$txtAFN': '199907120634',
                        'ctl00$ContentPlaceHolder1$GridView1$ctl05$txtDocumentID': '10255843',
                    }

            test_headers = {
                "Origin": "https://recorder.cuyahogacounty.us",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3"
                    }

            yield FormRequest(
                url='https://recorder.cuyahogacounty.us/Searchs/Parcellist.aspx',
                formdata=mortgage_form_data,
                meta={'parcel_id': response.meta['parcel_id']},
                dont_filter=True,
                # headers=test_headers,
                callback=self.mortgage_processor
            )

        property_object.save()
        # else:
        #     property_object.save()
        #     print('no deed')






