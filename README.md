# intro

the goal here is just to scrape some flight prices for some routes from kayak.

# method

setup a chrome web driver with selenium

parse the inputs from the user and build the url

load the page with selenium and parse it with beautiful soup

get times and prices for tickets returned after waiting for the page to load

use numpy to stack everything together

output to csv