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

resultsUrlBase = 'http://www.quicktricks.org/index.php?id=305&date='
javascriptLinkPattern = re.compile("javascript:onclick=popresults\(\'(.*)\',.*")
recapUrlBase = 'http://www.quicktricks.org/'
basePath = '/Users/frice/PycharmProjects/bridge/results/'

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
    resultsUrl = resultsUrlBase + day.strftime("%m/%d/%y")
    print(resultsUrl)
    resultsPage = fetchPage(resultsUrl)
    resultsSoup = BeautifulSoup(resultsPage, 'html.parser')
    resultsDiv = resultsSoup.find('div', class_="tx-bridgeresults-pi1")
    recapLinks = resultsDiv.find_all('a', href=re.compile("recap"))
    for recapLink in recapLinks:
        javascriptLink = recapLink['href']
        match = javascriptLinkPattern.match(javascriptLink)
        if(match):
            recapLink = recapUrlBase + match.group(1)
            print(recapLink)
            recapPage = fetchPage(recapLink)
            filename = recapLink.split("/")[-1]
            filePath = resultsPath / filename
            print(filePath)
            with open(filePath, 'wb') as recapFile:
                recapFile.write(recapPage)


while(resultsDay > earliestResults):
    print("Considering "+ resultsDay.isoformat())
    fetchResults(resultsDay)
    resultsDay -= datetime.timedelta(7)