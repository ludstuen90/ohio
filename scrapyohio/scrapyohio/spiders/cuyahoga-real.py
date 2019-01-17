# -*- coding: utf-8 -*-
import datetime
import pickle

import scrapy
from scrapy import FormRequest
from scrapy.exceptions import CloseSpider

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

        continue_where_last_scrape_left_off = False
        seven_days_ago = datetime.datetime.today() - datetime.timedelta(days=7)

        self.cuyahoga_county_object, created = models.County.objects.get_or_create(name="Cuyahoga")

        if continue_where_last_scrape_left_off:
            self.all_cuyahoga_properties = models.Property.objects.filter(county=self.cuyahoga_county_object,
                                                                        ).exclude(
                                                                    last_scraped_one__gte=seven_days_ago
                                                                    ).order_by('?')
        else:
            self.all_cuyahoga_properties = models.Property.objects.filter(county=self.cuyahoga_county_object,
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
        for package in self.retrieve_all_warren_county_urls():
            form_data['ParcelID'] = package['parcel_id']

            yield FormRequest(
                    url=package['url'],
                    formdata=form_data,
                    method='POST',
                    meta={'page': 1, 'parcel_id': package['parcel_id']},
                    dont_filter=True,
                    headers=HEADERS,
            )

    def parse(self, response, *args, **kwargs):
        """

        :param response:
        :return:
        """
        if response.url == 'https://recorder.cuyahogacounty.us/LockedOut.aspx':
            # If we recive this page, it's because our IP address has been blocked!
            raise CloseSpider('ip_address_blocked')

        print("RESPONSE URL: ", response.url)

        soup = BeautifulSoup(response.text, 'html.parser')
        property_object = models.Property.objects.get(parcel_number=response.meta['parcel_id'])
        primary_owner = property_object.owner
        deed_date = utils.parse_recorder_items(soup, primary_owner, 'DEED')
        property_object.last_scraped_one = datetime.datetime.now()
        if deed_date:
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

            property_object.save()
        else:
            property_object.save()
            print('no deed')






