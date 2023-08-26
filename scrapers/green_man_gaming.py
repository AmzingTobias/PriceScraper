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

# Host name for the green man gaming website
GREEN_MAN_GAMING_HOST_NAME = "www.greenmangaming.com"


class GreenManGaming(Scraper):
    """
    A scraper for the Green man gaming website
    """

    def __init__(self, url: str) -> None:
        """
        :param url: The Green man gaming product URL
        """
        super().__init__(url)

    @staticmethod
    def _parse_response_for_price(parsed_source: BeautifulSoup) -> float:
        """
        Parse a response received from scraping the green man gaming website to find the price
        :param parsed_source: The source received from the green man gaming website, that has been parsed to a
         BeautifulSoup object
        :return: The price of the product, or < 0 if no price was found
        """
        # Attempt to find the span flag which contains the price
        product_details = parsed_source.find('gmgprice', class_="current-price pdp-price")
        if product_details is not None:
            if len(product_details.text) > 0:
                try:
                    product_price = product_details.text[1:]
                    log_price_found_from_request(float(product_price))
                    return float(product_price)
                except ValueError:
                    log_price_invalid()
                    pass
            else:
                logging.error(f"Price could not be found in {product_details}")
        else:
            logging.error(f"Price could not be found from {parsed_source.prettify()}")
        return -1.0

    def get_product_info(self) -> PriceInfo | None:
        """
        Scrape the green man gaming website to get the product info
        :return: The product info that was found from the URL, or None if no product information was found
        """
        log_url_request(self.url)
        # Check the URL is a valid green man gaming link
        if validate_url(self.url, GREEN_MAN_GAMING_HOST_NAME):
            try:
                # Make the request for the price
                scrape_request = requests.request("GET", self.url, headers=HEADERS)
                # Check that the request succeeded
                if scrape_request.status_code == requests.codes["ok"]:
                    # Use the source code to parse
                    parsed_source = BeautifulSoup(scrape_request.text, 'lxml')
                    scrape_request.close()
                    product_price = self._parse_response_for_price(parsed_source)
                    return PriceInfo(product_price, self.url, datetime.date.today())
                else:
                    log_invalid_request(scrape_request.status_code)
                    scrape_request.close()
            except requests.exceptions.ConnectionError:
                logging.error("Connection error occurred")
        return None


if __name__ == '__main__':
    print(f"{GreenManGaming.__name__}:\n{GreenManGaming.__doc__}")
    for name, method in GreenManGaming.__dict__.items():
        if callable(method) and hasattr(method, '__doc__'):
            docstring = method.__doc__
            if docstring:
                print(f"Method '{name}':\n{docstring.strip()}\n")
