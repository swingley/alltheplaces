# -*- coding: utf-8 -*-
import scrapy
import json
import re
from uszipcode import ZipcodeSearchEngine
from locations.items import GeojsonPointItem

STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
          'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
          'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
          'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']


class AldiSpider(scrapy.Spider):
    name = "aldi"
    allowed_domains = ["aldi.us"]
        
    def start_requests(self):
        for state in STATES:
            yield scrapy.Request(
                'https://aldi.us/stores/en-us/Search?SingleSlotGeo={}&Mode=None'.format(state),
                callback = self.parse
            )
    
    def parse(self, response):
        selector = scrapy.Selector(response)
        stores = selector.css('.resultItem')
        for store in stores:
            json_data = json.loads(store.css('.resultItem::attr(data-json)').extract_first())
            ref = json_data['id']
            lat = json_data['locY']
            lon = json_data['locX']
            name = store.css('.resultItem-CompanyName::text').extract_first()
            street = store.css('.resultItem-Street::text').extract_first()
            address1 = store.css('.resultItem-City::text').extract_first().split(',')
            hours_data = store.css('.openingHoursTable > tr')
            
            pattern = r'(.*?)(\s|,\s)([0-9]{1,5})'
            if len(address1) == 2: 
                city = address1[0]
                match = re.search(pattern, address1[1].strip())
                state = match.groups()[0]
                zipcode = match.groups()[2]

            elif len(address1) == 1:
                match = re.search(pattern, address1[0].strip())
                city, state, zipcode = match.groups()

            properties = {
                'ref': ref,
                'name': name,
                'opening_hours': self.hours(hours_data),
                'lat': lat,
                'lon': lon,
                'street': street,
                'city': city,
                'state': state,
                'postcode': zipcode
            }

            yield GeojsonPointItem(**properties)

    def hours(self, data):
        opening_hours = ''
        for day_group in data:
            time = day_group.css('td::text').extract()
            day = time[0].strip()
            hours = time[1].strip()

            if '-' in day:
                f_day = day.split('-')[0].strip()[:2]
                t_day = day.split('-')[1].strip()[:2]
                day = '{}-{}'.format(f_day, t_day)
            else:
                day = day[:2]
            if hours == 'closed' :
                opening_hours += '{} {};'.format(
                    day,
                    hours
                )
            else :
                f_hour_text = hours.split('-')[0].strip()
                t_hour_text = hours.split('-')[1].strip()
                f_hour = self.normalize_time(f_hour_text)
                t_hour = self.normalize_time(t_hour_text)
                opening_hours += '{} {}; '.format(
                    day,
                    '{}-{}'.format(f_hour, t_hour)
                )

        return opening_hours

    def normalize_time(self, time_str):
        match = re.search(r'([0-9]{1,2}):([0-9]{1,2}) (A|P)M$', time_str)
        if not match:
            match = re.search(r'([0-9]{1,2}) (A|P)M$', time_str)
            h, am_pm = match.groups()
            m = "0"
        else:
            h, m, am_pm = match.groups()

        return '%02d:%02d' % (
            int(h) + 12 if am_pm == 'P' else int(h),
            int(m),
        )



            




    
