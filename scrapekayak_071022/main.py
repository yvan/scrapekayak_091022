"""
example:

python main.py --baseurl https://www.kayak.de/flights --destination JFK --origin=BER -rd 2022-11-13 -dd 2022-11-06

kill drivers when done:

pkill -f /Applications/Google Chrome.app
pkill -f drivers/chromedriver
"""

# std
import os
import re
import sys
import time
import pathlib
import argparse
import datetime

# numerical
import numpy as np

# html
from bs4 import BeautifulSoup

# selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

# web driver
from webdriver_manager.chrome import ChromeDriverManager

# setup global web driver code
chrome_options = webdriver.ChromeOptions()
# s = Service("")
# driver = webdriver.Chrome(service=s)
# ~/.wdm/drivers/chromedriver/mac64/105.0.5195/chromedriver
driver = webdriver.Chrome(ChromeDriverManager().install())
driver.implicitly_wait(20)

# builds a url for a one-way flight
# OR a two-way flight
def buildUrl(baseUrl: str,
             origin: str,
             ddate: str,
             destination: str|None=None,
             rdate: str|None=None) -> str:
    # build a two way url
    if rdate:
        return f"{baseUrl}/{origin}-{destination}/{ddate}/{rdate}"
    # build a one way url
    else:
        return f"{baseUrl}/{origin}/{ddate}"

def loadPage(url):
    driver.get(url)

def getText(seq):
    return [s.getText() for s in seq]


"""
This function parses string currency data. An example of currency
formats we can parse here:

1.171
1.171,54
1.171,5
"""
def currencyParse(currencyStr, dropchange=True):
    priceChange = currencyStr.split(",")
    if len(priceChange) > 1:
        price = re.sub("[.,]", "", priceChange[0])
        change = priceChange[1]
    else:
        price = re.sub("[.,]", "", priceChange[0])
        change = 0
    if dropchange:
        return price
    return f"{price}.{change}"
    
        
if __name__ == "__main__":
    # process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s","--sleeptime",default=30)
    parser.add_argument("-p","--savepath",
                        default=os.path.expanduser("~/projects/datasets/scrapekayak_071022/"))
    parser.add_argument("-b","--baseurl", default="https://www.kayak.de/flights")
    parser.add_argument("-o","--origin", default="BER")
    parser.add_argument("-d","--destination", default="JFK")
    parser.add_argument("-rd","--dreturn", default="2022-11-13")
    parser.add_argument("-dd","--ddepart", default="2022-11-06")
    arguments = parser.parse_args()
    
    # setup
    DATAPATH = arguments.savepath        
    baseUrl = arguments.baseurl
    ddate = arguments.ddepart
    rdate = arguments.dreturn
    origin = arguments.origin
    destination = arguments.destination

    # get the page
    url = buildUrl(baseUrl, origin, ddate, destination, rdate)
    loadPage(url)
    print(f"Sleeping for {arguments.sleeptime} seconds to load page data...")
    time.sleep(arguments.sleeptime)

    # if the page has no results (nonsense inputs or error)

    # cook a soup
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # first get all the divs containing results
    results = soup.find_all('div', attrs={"class":"resultInner"})

    # then search the results for things
    rawtimes = []
    rawprice = []
    currency = []
    for res in results:
        # time
        timeDivs = res.find_all('span', attrs={"class":"base-time"})
        rawtimes.append(getText((timeDivs[0], timeDivs[1])))
        
        # prices and currencies, split up
        priceElems = res.find_all('span', attrs={"id":re.compile("([a-zA-Z0-9\-]+)price-text")})
        priceTexts = [span.getText().split() for span in priceElems]
        priceValue = []
        for p,_ in priceTexts:
            try:
                priceValue.append(int(p))
            except ValueError:
                priceValue.append(int(currencyParse(p)))
        priceCurrency = [v for _, v in priceTexts]
        bestpriceIdx, worstpriceIdx = np.argmin(priceValue), np.argmax(priceValue)
        rawprice.append([priceValue[bestpriceIdx], priceValue[worstpriceIdx]])
        currency.append([priceCurrency[bestpriceIdx], priceCurrency[worstpriceIdx]])

    times = np.array(rawtimes)
    prices = np.array(rawprice)
    currencies = np.array(currency)
    sources = np.array(times.shape[0]*[[origin]])
    destinations = np.array(times.shape[0]*[[destination]])
    flightdata = np.hstack((sources, destinations, rawtimes, rawprice, currency,))
    
    # combine and save to csv    
    today = datetime.datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
    path = pathlib.Path(DATAPATH, f'kayak_{today}_{origin}_{ddate}_{destination}_{rdate}.csv')
    np.savetxt(path, flightdata, delimiter=",", fmt="%s")
    
