# std
import os
import re
import sys
import getopt

# numerical
import numpy as np

# bs
from bs4 import BeautifulSoup

# selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
# web driver
from webdriver_manager.chrome import ChromeDriverManager

# setup global web driver code
chrome_options = webdriver.ChromeOptions()
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
        
if __name__ == "__main__":
    ddate = "2022-11-06"
    rdate = "2022-11-13"
    origin = "BER"
    destination = "JFK"
    baseUrl = "https://www.kayak.de/flights"

    # urlS = buildUrl(baseUrl, origin, ddate)
    url = buildUrl(baseUrl, origin, ddate, destination, rdate)
    loadPage(url)

    # get webpage
    soup = BeautifulSoup(driver.page_source, 'lxml')

    # first get all the divs containing times/prices, etc
    results = soup.find_all('div', attrs={"class":"resultInner"})

    # then search the results for things
    rawtimes = []
    rawprice = []
    currency = []
    for res in results:
        # time
        timeDivs = res.find_all('span', attrs={"class":"base-time"})
        rawtimes.append([getText([timeDivs[i], timeDivs[i+1]]) for i in range(0,len(timeDivs),2)])
        # price values and currencies split up
        priceElems = res.find_all('span', attrs={"id":re.compile("([a-zA-Z0-9\-]+)price-text")})
        priceTexts = [span.getText().split() for span in priceElems]
        priceValue = [int(p) for p,_ in priceTexts]
        priceCurrency = [v for _, v in priceTexts]
        
        bestpriceIdx, worstpriceIdx = np.argmin(priceValue), np.argmax(priceValue)
        rawprice.append([priceValue[bestpriceIdx], priceValue[worstpriceIdx]])
        currency.append([priceCurrency[bestpriceIdx], priceCurrency[worstpriceIdx]])

    times = np.array(rawtimes)
    prices = np.array(rawprice)
    currencies = np.array(currency)

    x = 5


    # # times
    # departArriveClass = {"class":"base-time".split()}
    # timeDivs = soup.find_all('span', attrs=departArriveClass)
    # rawtimes = [getText([timeDivs[i], timeDivs[i+1]]) for i in range(0,len(timeDivs),2)]
    # times = np.array(rawtimes)

    # # prices
    # regex = re.compile(r'.*-price-text')
    # priceClasses = {"class": regex}
    # priceDivs = soup.find_all('span', attrs=priceClasses)
    # rawPrices = [getText([priceDivs[i],priceDivs[i+1]]) for i in range(0,len(priceDivs))]
    # prices = np.array(rawPrices)
    
    # longparams = ["origin=", "destination="]
    # result = getopt.getopt(sys.argv[1:], "", longparams)
    
