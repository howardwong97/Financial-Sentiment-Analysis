import requests
from bs4 import BeautifulSoup, SoupStrainer
import pandas as pd
import time


def search_term(text):
    query = '('
    textlist = text.split(' OR ')
    for idx, t in enumerate(textlist):
        if len(t.split(' ')) == 2:
            query = query + '%22' + t.split(' ')[0] + '%20' + t.split(' ')[1] + '%22'
        else:
            query = query + '%20' + t
        if idx != len(textlist) - 1:
            query = query + '%20OR'
    return query + ')'


dates = pd.date_range('2020-07-18', '2020-10-18', freq='1D')
dates = [i.strftime('%Y%m%d%H%M%S') for i in dates]  # requires format YYYYMMDDHHMMSS
query = search_term('AAPL OR apple')
base_url = 'https://api.gdeltproject.org/api/v2/doc/doc?'
links = []

for i in range(len(dates) - 1):
    t0, t1 = dates[i], dates[i + 1]
    url = base_url + 'query={}&mode=artlist&maxrecords=250&startdatetime={}&enddatetime={}'.format(query, t0, t1)
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'lxml')

    for link in BeautifulSoup(res.content, 'html.parser', parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            links.append(link['href'])
    time.sleep(10)

with open('aapl_links.txt', 'w') as f:
    for item in links:
        f.write("%s\n" % item)