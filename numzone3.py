"""
only python3
numzones3 US: get timeone info from US numbers or area code
database source: https://www.allareacodes.com/area-code-list.htm

from wikipedia: https://simple.wikipedia.org/wiki/List_of_U.S._states_by_time_zone
These are the times zones that are used by the United States and its territories:
UTC-11: Samoa Standard Time
UTC-10: Hawaii-Aleutian Standard Time (HST)
UTC-9: Alaska Standard Time (AKST)
UTC-8: Pacific Standard Time (PST)
UTC-7: Mountain Standard Time (MST)
UTC-6: Central Standard Time (CST)
UTC-5: Eastern Standard Time (EST)
UTC-4: Atlantic Standard Time (AST)
UTC+10: Chamorro Standard Time

"""
import requests
from bs4 import BeautifulSoup
import sys
import re
from django.conf import settings
import json
from django.db.utils import IntegrityError

named_zonetable = {
    'PST': 'UTC-8',
    'MST': 'UTC-7',
    'CST': 'UTC-6',
    'EST': 'UTC-5',
    'AST': 'UTC-4'
}


def rebuild_database():
    url = 'https://www.allareacodes.com/area-code-list.htm'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    response = requests.get(url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    row_div = soup.find('div', class_="row search-min-height")

    numzones = {
        "0": {
            "address": "",
            "timezone": "UTC+0",
            "state": ""
        }
    }
    for div in row_div.find_all('div', class_="col-xs-12 col-md-6"):
        if 'Area Code Listings by Number' in div.find('h2').get_text():
            table = div.find('table')
            for tr in table.find_all('tr'):
                if tr.has_attr('class') and 'header_row' in tr['class']:
                    continue
                area_code_src = str(tr.find_all('td')[0])
                state_src = str(tr.find_all('td')[1])

                area_code = tr.find_all('td')[0].find('a').get_text()  # type:str
                state = tr.find_all('td')[1].find('a').get_text()  # type:str

                tag_html = str(tr.find_all('td')[1])  # type:str
                tz_name = re.findall('<br/>([A-Z]+|\([A-Z-+0-9]+\))', tag_html)  # type:str
                address = re.findall('</a>:(.+?)<br', tag_html)  # type:str

                if not len(tz_name):
                    print('timezone name cannot be parsed, parsed: {}, source text: {}'.format(tz_name, tag_html))
                    sys.exit()
                if len(tz_name) > 1:
                    print('multiple timezone: {} source text: {}'.format(tz_name, tag_html))
                    sys.exit()

                if not len(address):
                    print('address cannot be parsed, parsed: {}, source text: {}'.format(address, tag_html))
                    sys.exit()
                if len(address) > 1:
                    print('multiple address: {} source text: {}'.format(address, tag_html))
                    sys.exit()

                area_code = area_code.strip()
                state = state.strip()
                timezone_name = tz_name[0].strip().strip('()')
                address = address[0].strip()

                if not area_code:
                    print('no area code parsed from source text: {}'.format(area_code_src))
                    sys.exit()
                if not state:
                    print('no state parsed from source text: {}'.format(state_src))
                    sys.exit()
                if not timezone_name:
                    print('no timezone parsed from source text: {}'.format(tag_html))
                    sys.exit()
                if not address:
                    print('no address parsed from source text: {}'.format(tag_html))
                    sys.exit()

                numzones[area_code] = {
                    'timezone': timezone_name,
                    'state': state,
                    'address': address
                }
                print('area_code: {}, state: {} timezone: {} address: {}'.format(area_code, state, timezone_name, address))
    with open(settings.NUMZONE_DB_JSON_PATH, 'w') as f:
        f.write(json.dumps(numzones))
        print('{} saved'.format(settings.NUMZONE_DB_JSON_PATH))
