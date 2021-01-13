import datetime

import re
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import pathlib


today = datetime.date.today()
resultsDay = today - datetime.timedelta(today.weekday()) #fetch the last monday
earliestResults = datetime.date(2017, 1, 1)

resultsUrlBase = 'https://www.quicktricks.org/calendar-node-field-game-date-iso/day/'
javascriptLinkPattern = re.compile("javascript:onclick=popresults\(\'(.*)\',.*")
recapUrlBase = 'http://www.quicktricks.org/'
basePath = '/Users/frice/bridge/results/'

def fetchPage(url):
    try:
        with closing(get(url, stream=True)) as resp:
            content_type = resp.headers['Content-Type'].lower()
            if (resp.status_code == 200
                    and content_type is not None
                    and content_type.find('html') > -1):
                return resp.content
            else:
                return None

    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

def fetchResults(day):
    resultsPath = pathlib.Path(basePath + day.isoformat())
    if resultsPath.exists():
        print("Already fetched results for " + day.isoformat())
        return
    resultsPath.mkdir(parents=True, exist_ok=False)
    resultsUrl = resultsUrlBase + day.isoformat()
    print(resultsUrl)
    resultsPage = fetchPage(resultsUrl)
    #TODO better null handling
    if resultsPage is not None:
        resultsSoup = BeautifulSoup(resultsPage, 'html.parser')
        resultsDiv = resultsSoup.find('div', class_="calendar dayview")
    else:
        resultsDiv = None
    if resultsDiv:
        recap_links = resultsDiv.find_all('a', href=re.compile("recap"))
    else:
        recap_links = []
        print(f"skipping {day} recapDiv is none")
    print(recap_links)
    for recap_link in recap_links:
        recap_url = recap_link['href']
        recap_page = fetchPage(recap_url)
        if recap_page:
            filePath = resultsPath / "recap.html"
            with open(filePath, 'wb') as recapFile:
                recapFile.write(recap_page)
        else:
            print(f"skipping {day} page is none")

while(resultsDay > earliestResults):
    print("Considering "+ resultsDay.isoformat())
    fetchResults(resultsDay)
    resultsDay -= datetime.timedelta(7)