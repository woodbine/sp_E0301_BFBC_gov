# -*- coding: utf-8 -*-

#### IMPORTS 1.0

import os
import re
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup


#### FUNCTIONS 1.0

def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9QY][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9QY][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    now = datetime.now()
    year, month = date[:4], date[5:7]
    validYear = (2000 <= int(year) <= now.year)
    if 'Q' in date:
        validMonth = (month in ['Q0', 'Q1', 'Q2', 'Q3', 'Q4'])
    elif 'Y' in date:
        validMonth = (month in ['Y1'])
    else:
        try:
            validMonth = datetime.strptime(date, "%Y_%m") < now
        except:
            return False
    if all([validName, validYear, validMonth]):
        return True


def validateURL(url):
    try:
        r = urllib2.urlopen(url)
        count = 1
        while r.getcode() == 500 and count < 4:
            print ("Attempt {0} - Status code: {1}. Retrying.".format(count, r.status_code))
            count += 1
            r = urllib2.urlopen(url)
        sourceFilename = r.headers.get('Content-Disposition')

        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        else:
            ext = os.path.splitext(url)[1]
        validURL = r.getcode() == 200
        validFiletype = ext in ['.csv', '.xls', '.xlsx', '.docx']
        return validURL, validFiletype
    except:
        print ("Error validating URL.")
        return False, False


def validate(filename, file_url):
    validFilename = validateFilename(filename)
    validURL, validFiletype = validateURL(file_url)
    if not validFilename:
        print filename, "*Error: Invalid filename*"
        print file_url
        return False
    if not validURL:
        print filename, "*Error: Invalid URL*"
        print file_url
        return False
    if not validFiletype:
        print filename, "*Error: Invalid filetype*"
        print file_url
        return False
    return True


def convert_mth_strings ( mth_string ):
    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    for k, v in month_numbers.items():
        mth_string = mth_string.replace(k, v)
    return mth_string


#### VARIABLES 1.0

entity_id = "E0301_BFBC_gov"
url = 'http://data.bracknell-forest.gov.uk/Download/finance/payments-over-500?page={}'
errors = 0
data = []


#### READ HTML 1.0

html = urllib2.urlopen(url)
soup = BeautifulSoup(html, 'lxml')


#### SCRAPE DATA
import itertools

for pages in itertools.count(1):
    n=str(pages)
    html = urllib2.urlopen(url.format(n))
    soup = BeautifulSoup(html, 'lxml')
    links = soup.find_all('a', 'download button green CSV')
    for link in links:
        link_csv = 'http://data.bracknell-forest.gov.uk' + link['href']
        csvYr = link['href'].split('CSV')[0].split('/')[-2].split('-')[-1]
        if 'january-to-march' in link['href']:
            csvMth = 'Q1'
        if 'april-to-june' in link['href']:
            csvMth = 'Q2'
        if 'july-to-september' in link['href']:
            csvMth = 'Q3'
        if 'october-to-december' in link['href']:
            csvMth = 'Q4'
        if '-to-' not in link['href']:
            csvMth = link['href'].split('CSV')[0].split('/')[-2].split('-')[-2][:3]
        if 'september' in csvYr:
            csvYr = '2015'
        if 'june-to-september' in link['href']:
            csvMth = 'Q0'
        if 'february-to-may' in link['href']:
            csvMth = 'Q0'
        csvMth = convert_mth_strings(csvMth.upper())
        data.append([csvYr, csvMth, link_csv])
    block = soup.find('td', attrs = {'colspan':'4'})
    url_pages = block.find_all('a')
    if ">" not in  url_pages[-1].text:
            break

#### STORE DATA 1.0

for row in data:
    csvYr, csvMth, url = row
    filename = entity_id + "_" + csvYr + "_" + csvMth
    todays_date = str(datetime.now())
    file_url = url.strip()

    valid = validate(filename, file_url)

    if valid == True:
        scraperwiki.sqlite.save(unique_keys=['f'], data={"l": file_url, "f": filename, "d": todays_date })
        print filename
    else:
        errors += 1

if errors > 0:
    raise Exception("%d errors occurred during scrape." % errors)


#### EOF
