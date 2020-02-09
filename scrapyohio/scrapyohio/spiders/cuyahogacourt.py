# -*- coding: utf-8 -*-
import os
import re
import csv


import scrapy
from bs4 import BeautifulSoup
from scrapy import FormRequest

from ohio import settings

class CuyahogaCourtsScraper(scrapy.Spider):
    handle_httpstatus_all = True
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
        "Accept": "*/*",
        "X-MicrosoftAjax": "Delta=true",
        "X-Requested-With": "XMLHttpRequest",
        "Cache-Control": "no-cache",
        "Origin": "https://cpdocket.cp.cuyahogacounty.us",
        "Info": "The Ohio Center for Investigative Journalism, Eye on Ohio, is requesting these public records for "
        "use in a journalism project, and to conserve valuable public funds and government employees' time "
        "instead of filing multiple freedom of information act requests.",
        "Questions": "If you have questions or concerns, please contact Lucia Walinchus at 646-397-7761 or "
         "Lucia[the at symbol}eyeonohio.com.",
    }

    name = 'cuyahogacourt'
    allowed_domains = ['cpdocket.cp.cuyahogacounty.us']

    def retrieve_all_cuyahoga_county_urls(self):
        script_dir = os.path.dirname(__file__)  # <-- absolute dir this current script is in
        rel_path = "../scraper_data_drops/Cuyahoga Land Bank Transfers.CSV"
        rel_path_script = "../../cuyahoga_court_results.txt"
        "/home/lukas/codigo/property_project_ohio/scrapyohio/scrapyohio/scraper_data_drops/Cuyahoga Land Bank Transfers.CSV"
        """
        
f= open("/home/lukas/codigo/property_project_ohio/scrapyohio/cuyahoga_court_results.txt","r")

array_of_known_ids = []
items = csv.reader(f, delimiter=";")   

for x in items: 
    print(x[0])
    array_of_known_ids.append(x[0])


not_found_array = []
with open("/home/lukas/codigo/property_project_ohio/scrapyohio/scrapyohio/scraper_data_drops/Cuyahoga Land Bank Transfers.CSV", "r") as file:
    reader = csv.reader(file)
    for row in reader:
        if row[4] not in array_of_known_ids:
            not_found_array.append(row[4])
         
        """
        abs_file_path = os.path.join(script_dir, rel_path)

        list_of_ids_already_processed = []
        abs_file_cuyahoga_path = os.path.join(script_dir, rel_path_script)
        with open(abs_file_cuyahoga_path,"r") as file:
            reader = csv.reader(file, delimiter=";")
            for row in reader:
                list_of_ids_already_processed.append(row[0])

        complete_list_of_all_parcel_ids_to_process = []
        with open(abs_file_path, "r") as file:
            reader = csv.reader(file)
            for iteration, row in enumerate(reversed(list(csv.reader(file)))):
                if iteration > 0:
                    if row[4] not in list_of_ids_already_processed:
                        complete_list_of_all_parcel_ids_to_process.append(row[4])

        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", len(complete_list_of_all_parcel_ids_to_process))
        for item in complete_list_of_all_parcel_ids_to_process:
            yield item

    def __init__(self):
        self.HEADERS.update(settings.CONTACT_INFO_HEADINGS)
        self.logged_out = False


    def start_requests(self):
        # We want to assign headers for each request triggered. Override the request object
        # sent over to include Lucia's contact information
        # for parameter_dictionary in self.retrieve_all_franklin_county_urls():

        # Use the enumerator function to allow an individual cookie jar for each request
        # This is necessary to keep track of multiple view states
        for enumerator, item in enumerate(self.retrieve_all_cuyahoga_county_urls()):
            yield scrapy.Request(
                url='https://cpdocket.cp.cuyahogacounty.us/tos.aspx',
                method='GET',
                callback=self.parse,
                meta={'dont_redirect': False, "parc_id": item,
                      'spider_num': enumerator, 'cookiejar': enumerator},
                dont_filter=True,
                headers=self.HEADERS
            )

    def parse(self, response):
        print("Here in response: ", response, "looking at ", response.meta['parc_id'])
        with open("examined_parcels.txt", 'w') as out_file:
            out_file.write(f"""{response.meta['parc_id']}\n""")

        # Load the foreclosure  search thing

        yield FormRequest.from_response(

            response,
            formdata={
                'ctl00$SheetContentPlaceHolder$btnYes': "Yes",
            },
            meta={"parc_id": response.meta['parc_id'],
                  'spider_num': response.meta['spider_num'], 'cookiejar': response.meta['spider_num']
                  },
            dont_filter=True,
            callback=self.initial_search,
            )

    def initial_search(self, response):
        yield FormRequest.from_response(
            response,
            url="https://cpdocket.cp.cuyahogacounty.us/Search.aspx",
            formdata={
                "__EVENTTARGET": "ctl00$SheetContentPlaceHolder$rbCivilForeclosure",
                "ctl00$SheetContentPlaceHolder$rbSearches": "forcl",
                "__ASYNCPOST": "true",
                "ctl00$ScriptManager1": "ctl00$SheetContentPlaceHolder$UpdatePanel1|ctl00$SheetContentPlaceHolder$rbCivilForeclosure"
            },
            meta={"parc_id": response.meta['parc_id'],
                  'spider_num': response.meta['spider_num'], 'cookiejar': response.meta['spider_num']
                  },
            headers={"Origin": "https://cpdocket.cp.cuyahogacounty.us",
                        "Upgrade-Insecure-Requests": "1",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
                        "Sec-Fetch-User": "?1",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        },
                                    dont_filter=True,
            callback=self.real_search_page,
        )

    def goodies_page(self, response):
        # open_in_browser(response)
        soup = BeautifulSoup(response.body, 'html.parser')
        prayer_amount = soup.find("td", text=re.compile("Prayer Amount:"), class_="tdtitle").find_next().text
        print("PRAYER AMOUNT AL FINAL: ", prayer_amount)
        stripped_amount = prayer_amount.strip()


        case_number = soup.find("td", text=re.compile("Case Number:"), class_="tdtitle").find_next().text
        case_stripped = case_number.strip()

        filing_date = soup.find("td", text=re.compile("Filing Date:"), class_="tdtitle").find_next().text
        filing_date_stripped = filing_date.strip()

        print("Let's try stripping to see what we get:", stripped_amount, "!!!")
        with open('cuyahoga_court_results.txt', 'a') as file:
            file.write(f"""{response.meta['parc_id']};{case_stripped};{filing_date_stripped};{stripped_amount}\n""")

    def real_results(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        matched = soup.select('#__VIEWSTATE')
        if matched:
            viewstate_value = matched[0].get('value')

        vsg = soup.select('#__VIEWSTATEGENERATOR')
        if vsg:
            viewstategenerator_value = vsg[0].get('value')

        evg = soup.select('#__EVENTVALIDATION')
        if evg:
            eventvalidation_value = evg[0].get('value')

        yield FormRequest(
            "https://cpdocket.cp.cuyahogacounty.us/ForeclosureSearchResults.aspx",
            formdata={
                "__VIEWSTATE": viewstate_value,
                "__VIEWSTATEGENERATOR": viewstategenerator_value,
                    "__EVENTVALIDATION": eventvalidation_value,
                "__EVENTARGUMENT": "",
                "__EVENTTARGET": "ctl00$SheetContentPlaceHolder$ctl00$gvForeclosureResults$ctl02$lbCaseNum",
            },
            meta={"parc_id": response.meta['parc_id'],
                  'spider_num': response.meta['spider_num'], 'cookiejar': response.meta['spider_num']
                  },
            headers={"Origin": "https://cpdocket.cp.cuyahogacounty.us",
                     "Upgrade-Insecure-Requests": "1",
                     "Referer": "https://cpdocket.cp.cuyahogacounty.us/ForeclosureSearchResults.aspx",
                     "Content-Type": "application/x-www-form-urlencoded",
                     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
                     "Sec-Fetch-Mode": "navigate",
                     "Sec-Fetch-Site": "same-origin",
                     "Sec-Fetch-User": "?1",
                        "Upgrade-Insecure-Requests": "1",
                        "Host": "cpdocket.cp.cuyahogacounty.us",
                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
                     },
            dont_filter=True,
            callback=self.goodies_page,
        )

    def please_open(self, response):
        yield scrapy.Request(
            url='https://cpdocket.cp.cuyahogacounty.us/ForeclosureSearchResults.aspx',
            headers={"Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                     "Upgrade-Insecure-Requests": "1"
                        },
            method='GET',
            callback=self.real_results,
            meta={"parc_id": response.meta['parc_id'],
                  'spider_num': response.meta['spider_num'], 'cookiejar': response.meta['spider_num']},
            dont_filter=True,
        )

    def real_search_page(self, response):

        soup = BeautifulSoup(response.body, 'html.parser')

        yield FormRequest(
            "https://cpdocket.cp.cuyahogacounty.us/Search.aspx",
            formdata={
                "__EVENTARGUMENT": "",
                "__EVENTTARGET": "",
                "__LASTFOCUS": "",
                "__VIEWSTATE": "/wEPDwULLTEzMjA5Mjg3NzAPZBYCZg9kFgICAw9kFhQCAw9kFgICAQ9kFgQCAQ8WAh4EVGV4dAUPQ3V5YWhvZ2EgQ291bnR5ZAIDDxYCHwAFD0NsZXJrIG9mIENvdXJ0c2QCBQ8PFgIeB1Zpc2libGVoZGQCBw8PFgIfAWhkZAIJD2QWBAIDD2QWAgIBDxYCHwAF/gM8Zm9udCBmYWNlPSJBcmlhbCIgc2l6ZT0iNCI+PGI+Tk9USUNFOjwvYj5QdXJzdWFudCB0byBGZWRlcmFsIExhdyBhbmQgYXQgdGhlIGRpcmVjdGlvbiBvZiB0aGUgRG9tZXN0aWMgUmVsYXRpb25zIENvdXJ0LCBEb21lc3RpYyBWaW9sZW5jZSBjYXNlIGluZm9ybWF0aW9uIGlzIG5vIGxvbmdlciBhdmFpbGFibGUgdmlhIGludGVybmV0IGFjY2Vzcy4gIFB1cnN1YW50IHRvIGRpcmVjdGlvbiBmcm9tIHRoZSBDb21tb24gUGxlYXMgQ291cnQgZ2VuZXJhbCBEaXZpc2lvbiwgQ2l2aWwgU3RhbGtpbmcgUHJvdGVjdGlvbiBPcmRlciBjYXNlcyBhcmUgYWxzbyBub3QgYXZhaWxhYmxlIG9uIHRoZSBpbnRlcm5ldC4gIENhc2UgaW5mb3JtYXRpb24gbWF5IGJlIG9idGFpbmVkIGluIHBlcnNvbiBhdCB0aGUgQ2xlcmsgb2YgQ291cnRzJyBvZmZpY2VzIG9yIGJ5IGNvbnRhY3RpbmcgdGhlIENsZXJrJ3MgZG9ja2V0IGluZm9ybWF0aW9uIGxpbmUgYXQgMjE2LTQ0My03OTUwLjwvZm9udD48L1A+DQoNCg0KDQpkAgUPZBYCZg9kFhYCAw8WAh8BaGQCCQ8QDxYCHgdDaGVja2VkZ2RkZGQCFQ9kFgJmD2QWDAIDDxBkDxYIZgIBAgICAwIEAgUCBgIHFggQBQhbU0VMRUNUXWVnEAUSQk9BUkQgT0YgUkVWSVNJT05TBQJCUmcQBQVDSVZJTAUCQ1ZnEAUSRE9NRVNUSUMgUkVMQVRJT05TBQJEUmcQBQtHQVJOSVNITUVOVAUCR1JnEAUNSlVER01FTlQgTElFTgUCSkxnEAUUTUlTQ0VMTEFORU9VUy1DTEFJTVMFAk1TZxAFDlNQRUNJQUwgRE9DS0VU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OTkyBQQxOTkyZxAFBDE5OTEFBDE5OTFnEAUEMTk5MAUEMTk5MGcQBQQxOTg5BQQxOTg5ZxAFBDE5ODgFBDE5ODhnEAUEMTk4NwUEMTk4N2cQBQQxOTg2BQQxOTg2ZxAFBDE5ODUFBDE5ODVnEAUEMTk4NAUEMTk4NGcQBQQxOTgzBQQxOTgzZxAFBDE5ODIFBDE5ODJnEAUEMTk4MQUEMTk4MWcQBQQxOTgwBQQxOTgwZxAFBDE5NzkFBDE5NzlnEAUEMTk3OAUEMTk3OGcQBQQxOTc3BQQxOTc3ZxAFBDE5NzYFBDE5NzZnEAUEMTk3NQUEMTk3NWcQBQQxOTc0BQQxOTc0ZxAFBDE5NzMFBDE5NzNnEAUEMTk3MgUEMTk3MmcQBQQxOTcxBQQxOTcxZxAFBDE5NzAFBDE5NzBnEAUEMTk2OQUEMTk2OWcQBQQxOTY4BQQxOTY4ZxAFBDE5NjcFBDE5NjdnEAUEMTk2NgUEMTk2NmcQBQQxOTY1BQQxOTY1ZxAFBDE5NjQFBDE5NjRnEAUEMTk2MwUEMTk2M2cQBQQxOTYyBQQxOTYyZxAFBDE5NjEFBDE5NjFnEAUEMTk2MAUEMTk2MGcQBQQxOTU5BQQxOTU5ZxAFBDE5NTgFBDE5NThnEAUEMTk1NwUEMTk1N2cQBQQxOTU2BQQxOTU2ZxAFBDE5NTUFBDE5NTVnEAUEMTk1NAUEMTk1NGcQBQQxOTUzBQQxOTUzZxAFBDE5NTIFBDE5NTJnEAUEMTk1MQUEMTk1MWcQBQQxOTUwBQQxOTUwZxAFBDE5NDkFBDE5NDlnEAUEMTk0OAUEMTk0OGcQBQQxOTQ3BQQxOTQ3ZxAFBDE5NDYFBDE5NDZnEAUEMTk0NQUEMTk0NWcQBQQxOTQ0BQQxOTQ0ZxAFBDE5NDMFBDE5NDNnEAUEMTk0MgUEMTk0MmcQBQQxOTQxBQQxOTQxZxAFBDE5NDAFBDE5NDBnEAUEMTkzOQUEMTkzOWcQBQQxOTM4BQQxOTM4ZxAFBDE5MzcFBDE5MzdnEAUEMTkzNgUEMTkzNmcQBQQxOTM1BQQxOTM1ZxAFBDE5MzQFBDE5MzRnEAUEMTkzMwUEMTkzM2cQBQQxOTMyBQQxOTMyZxAFBDE5MzEFBDE5MzFnEAUEMTkzMAUEMTkzMGcQBQQxOTI5BQQxOTI5ZxAFBDE5MjgF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cmJDaXZpbENhc2UFKWN0bDAwJFNoZWV0Q29udGVudFBsYWNlSG9sZGVyJHJiQ2l2aWxDYXNlBSljdGwwMCRTaGVldENvbnRlbnRQbGFjZUhvbGRlciRyYkNpdmlsTmFtZQUpY3RsMDAkU2hlZXRDb250ZW50UGxhY2VIb2xkZXIkcmJDaXZpbE5hbWUFMGN0bDAwJFNoZWV0Q29udGVudFBsYWNlSG9sZGVyJHJiQ2l2aWxGb3JlY2xvc3VyZQUmY3RsMDAkU2hlZXRDb250ZW50UGxhY2VIb2xkZXIkcmJDckNhc2UFJmN0bDAwJFNoZWV0Q29udGVudFBsYWNlSG9sZGVyJHJiQ3JDYXNlBSZjdGwwMCRTaGVldENvbnRlbnRQbGFjZUhvbGRlciRyYkNyTmFtZQUmY3RsMDAkU2hlZXRDb250ZW50UGxhY2VIb2xkZXIkcmJDck5hbWUFJ2N0bDAwJFNoZWV0Q29udGVudFBsYWNlSG9sZGVyJHJiQ29hQ2FzZQUnY3RsMDAkU2hlZXRDb250ZW50UGxhY2VIb2xkZXIkcmJDb2FDYXNlBSdjdGwwMCRTaGVldENvbnRlbnRQbGFjZUhvbGRlciRyYkNvYU5hbWUFJ2N0bDAwJFNoZWV0Q29udGVudFBsYWNlSG9sZGVyJHJiQ29hTmFtZQU8Y3RsMDAkU2hlZXRDb250ZW50UGxhY2VIb2xkZXIkZm9yZWNsb3N1cmVTZWFyY2gkaW1nYnRuTnVtYmVyBTtjdGwwMCRTaGVldENvbnRlbnRQbGFjZUhvbGRlciRmb3JlY2xvc3VyZVNlYXJjaCRpbWdidG5EYXRlMgU6Y3RsMDAkU2hlZXRDb250ZW50UGxhY2VIb2xkZXIkZm9yZWNsb3N1cmVTZWFyY2gkaW1nYnRuRGF0ZQU4Y3RsMDAkU2hlZXRDb250ZW50UGxhY2VIb2xkZXIkZm9yZWNsb3N1cmVTZWFyY2gkY2JTdGF0dXMFOWN0bDAwJFNoZWV0Q29udGVudFBsYWNlSG9sZGVyJGZvcmVjbG9zdXJlU2VhcmNoJGNiQlJDYXNlcwVAY3RsMDAkU2hlZXRDb250ZW50UGxhY2VIb2xkZXIkZm9yZWNsb3N1cmVTZWFyY2gkY2JCYW5rcnVwdGN5U3RheWPDhcVoVixGVeJC9aCJ8MPq0xbJJrDyCtq8YzEJTr56",
                "__VIEWSTATEGENERATOR": "BBBC20B8",
                "__EVENTVALIDATION": "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",
                "__ASYNCPOST": "true",
                "__LASTFOCUS": "",
                "__EVENTARGUMENT": "",
                "__EVENTTARGET": "",
                "ctl00$ScriptManager1": "ctl00$SheetContentPlaceHolder$UpdatePanel1|ctl00$SheetContentPlaceHolder$foreclosureSearch$btnSubmit",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$FRMaskedEditExtender_ClientState": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$TOMaskedEditExtender_ClientState": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$btnSubmit": "Submit Search",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$ddlCaseYear": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$ddlFilingType": "1467",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$meeParcelNbr_ClientState": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$meeZip_ClientState": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$txtCaseSequence": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$txtCity": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$txtFromDate": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$txtParcelNbr": response.meta['parc_id'],
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$txtStreetName": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$txtStreetNbr": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$txtToDate": "",
                "ctl00$SheetContentPlaceHolder$foreclosureSearch$txtZip": "",
                "ctl00$SheetContentPlaceHolder$rbSearches": "forcl",
            },
            meta={"parc_id": response.meta['parc_id'],
                  'spider_num': response.meta['spider_num'], 'cookiejar': response.meta['spider_num']
                  },
            dont_filter=True,
            headers=self.HEADERS,
            callback=self.please_open,
        )

#  cat cuyahoga_court_results.txt | wc -l