import datetime
import json
import json
import logging
import re

import requests
from bs4 import BeautifulSoup

from common.product_info import PriceInfo
from common.scraper import validate_url, HEADERS, log_invalid_request, \
    log_url_request, log_price_invalid, log_price_found_from_request, Scraper, log_product_availability_from_request

# Host name for the CDkeys website
CDKEYS_HOST_NAME = "www.cdkeys.com"


class CDKeys(Scraper):
    """
    A scraper for the CDKeys website
    """

    def __init__(self, url: str) -> None:
        """
        :param url: The CDKeys product URL
        """
        super().__init__(url)

    @staticmethod
    def _parse_response_for_price(parsed_source: BeautifulSoup) -> float:
        """
        Parse a response received from scraping the CDKeys website to find the price
        :param parsed_source: The source received from the CDKeys website, that has been parsed to a
         BeautifulSoup object
        :return: The price of the product, or < 0 if no price was found
        """
        # Attempt to find the span flag which contains the price
        price_tag = parsed_source.find('span', id=re.compile(r"product-price-[0-9]*"))
        if price_tag is not None:
            # If the price is not None then attempt to access its attributes
            price_attribute: str = "data-price-amount"
            if price_attribute in price_tag.attrs:
                product_price: str = price_tag.attrs[price_attribute]
                try:
                    log_price_found_from_request(float(product_price))
                    return float(product_price)
                except ValueError:
                    log_price_invalid()
                    pass
            else:
                logging.error(f"Price could not be found in {price_tag.string}")
        else:
            logging.error(f"Price could not be found from {parsed_source.prettify()}")
        return -1.0

    @staticmethod
    def _parse_response_for_availability(parsed_source: BeautifulSoup) -> bool:
        """
        Parse a response received from scraping the CDKeys website to determine if a product is in stock
        :param parsed_source: The source received from the CDKeys website, that has been parsed to a
         BeautifulSoup object
        :return: True if the product is in stock, False otherwise
        """
        stock = parsed_source.find_all(class_="stock")
        # Sanity check
        if len(stock) > 0:
            try:
                availability: bool = json.loads(stock[0].attrs["data-mage-init"])["productAvailability"]["isAvailable"]
                log_product_availability_from_request(availability)
                return availability
            except KeyError:
                logging.error(f"Availability json could not be found from: \n{stock[0].attrs}")
            except json.JSONDecodeError:
                logging.error(f"The availability is not a valid json string: \n{stock[0].attrs['data-mage-init']}")
        return False

    def get_product_info(self) -> PriceInfo | None:
        """
        Scrape the CDkeys website to get the product info
        :return: The product info that was found from the URL, or None if no product information was found
        """
        log_url_request(self.url)
        # Check the URL is a valid CDKeys link
        if validate_url(self.url, CDKEYS_HOST_NAME):
            try:
                # Make the request for the price
                scrape_request = requests.request("GET", self.url, headers=HEADERS)
                # Check that the request succeeded
                if scrape_request.status_code == requests.codes["ok"]:
                    # Use the source code to parse
                    parsed_source = BeautifulSoup(scrape_request.text, 'lxml')
                    scrape_request.close()
                    product_price = self._parse_response_for_price(parsed_source)
                    product_availability = self._parse_response_for_availability(parsed_source)
                    if product_availability:
                        return PriceInfo(product_price, self.url, datetime.date.today())
                else:
                    log_invalid_request(scrape_request.status_code)
                    scrape_request.close()
            except requests.exceptions.ConnectionError:
                logging.error("Connection error occurred")
        return None


if __name__ == '__main__':
    print(f"{CDKeys.__name__}:\n{CDKeys.__doc__}")
    for name, method in CDKeys.__dict__.items():
        if callable(method) and hasattr(method, '__doc__'):
            docstring = method.__doc__
            if docstring:
                print(f"Method '{name}':\n{docstring.strip()}\n")
