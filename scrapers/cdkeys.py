import datetime
import logging
import re
import requests
from common.scraper import validate_url, HEADERS, STATUS_OK, log_invalid_request, \
    log_url_request, log_price_invalid, log_price_found_from_request, Scraper, log_product_availability_from_request
from bs4 import BeautifulSoup
import json
from common.product_info import ProductInfo

# Host name for the CDkeys website
CDKEYS_HOST_NAME = "www.cdkeys.com"


class CDKeys(Scraper):

    def __init__(self, url: str) -> None:
        super().__init__(url)

    def _parse_response_for_price(self, parsed_source: BeautifulSoup) -> float:
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

    def _parse_response_for_availability(self, parsed_source: BeautifulSoup) -> bool:
        stock = parsed_source.find_all(class_="stock")
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

    def get_product_info(self) -> ProductInfo | None:
        log_url_request(self.url)
        # Check the URL is a valid CDKeys link
        if validate_url(self.url, CDKEYS_HOST_NAME):
            try:
                # Make the request for the price
                scrape_request = requests.request("GET", self.url, headers=HEADERS)
                # Check that the request succeeded
                if scrape_request.status_code == STATUS_OK:
                    # Use the source code to parse
                    parsed_source = BeautifulSoup(scrape_request.text, 'lxml')
                    scrape_request.close()
                    product_price = self._parse_response_for_price(parsed_source)
                    product_availability = self._parse_response_for_availability(parsed_source)
                    return ProductInfo(product_price, product_availability)
                else:
                    log_invalid_request(scrape_request.status_code)
                    scrape_request.close()
            except requests.exceptions.ConnectionError:
                logging.error("Connection error occurred")
        return None


# def scrape_cdkeys(product_id: int, cdkeys_url: str) -> bool:
#     date_for_scrape = datetime.date.today()
#     scraper = CDKeys(cdkeys_url)
#     product_info = scraper.get_product_info()
#     new_low_found_for_day = False
#     if product_info.availability:
#         db = Manager()
#         current_price_for_product = db.get_price_for_product_with_date(product_id, date_for_scrape)
#         if current_price_for_product is not None:
#             if product_info.price < current_price_for_product.price:
#                 logging.info("Price found is lower than currently stored")
#                 new_low_found_for_day = db.add_price_for_product(product_id, product_info.price,
#                                                                  cdkeys_url, date_for_scrape)
#         else:
#             logging.info("New price added to database for day")
#             new_low_found_for_day = db.add_price_for_product(product_id, product_info.price,
#                                                              cdkeys_url, date_for_scrape)
#     return new_low_found_for_day



if __name__ == '__main__':
    # logging.error("This file should not be called manually")
    logging.basicConfig(level=logging.INFO)
    #
    # product_list = ["https://www.cdkeys.com/pc/star-wars-jedi-survivor-pc-origin-en",
    #                 "https://www.cdkeys.com/pc/starfield-premium-edition-pc-steam",
    #                 "https://www.cdkeys.com/pc/f1-manager-2023-pc-steam",
    #                 "https://www.cdkeys.com/pc/ratchet-and-clank-rift-apart-pc-steam",
    #                 "https://www.cdkeys.com/cyberpunk-2077-phantom-liberty-pc-dlc-gog"]
    # for product in product_list:
    #     scraper = CDKeys(product)
    #     product_info = scraper.get_product_info()