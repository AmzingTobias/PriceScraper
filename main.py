import logging
import random
import time

from common.product_info import PriceInfo
from common.scraper import validate_url
from config.config import Config
from database.product_database_manager import ProductDatabaseManager
from notifiers.discord import Discord
from scrapers.cdkeys import CDKEYS_HOST_NAME, CDKeys

config_manager = Config("config/config.json")


def compare_price_info(price_one: PriceInfo | None,
                       price_two: PriceInfo | None) -> PriceInfo | None:
    """
    Compare two prices, and return the lowest product information with the lowest price
    :param price_one: The first product price to check
    :param price_two: The second product price to check
    :return: The product information that has the lower price
    """
    if price_two is not None:
        if price_one is None or price_two.price < price_one.price:
            return price_two
    return price_one


def notify_of_current_lowest_price(product_name: str,
                                   current_lowest_price: PriceInfo,
                                   previous_price_info: PriceInfo,
                                   historical_low_price: PriceInfo) -> None:
    """
    Notify everyone required of a price change
    :param product_name: THe product name the price change was detected for
    :param current_lowest_price: The current lowest price that was found in the scrape
    :param previous_price_info: The last lowest price that was found in the scrape
    :param historical_low_price: The lowest price that was ever found
    """
    discord_notifier = Discord([config_manager.discord_webhook_url])
    discord_notifier.prepare_webhook(product_name, current_lowest_price, previous_price_info, historical_low_price)
    discord_notifier.send_webhook()


def scrape_sites():
    """
    Scrape all sites for all products that exist in the database, and send out notifications for any price changes that
    are found
    """
    product_database = ProductDatabaseManager("database/")
    all_product_ids = product_database.get_all_product_ids()
    for product_id in all_product_ids:
        all_source_sites_for_product = product_database.get_all_source_sites(product_id)
        lowest_price_info_found: PriceInfo | None = None
        for source_site in all_source_sites_for_product:
            url = source_site[1]
            if validate_url(url, CDKEYS_HOST_NAME):
                scraper = CDKeys(url)
                product_info_found = scraper.get_product_info()
                lowest_price_info_found = compare_price_info(lowest_price_info_found, product_info_found)
        if lowest_price_info_found is not None:
            previous_prices = product_database.get_prices_for_product(product_id)
            previous_price = PriceInfo(None, None, None)
            historical_low_price: PriceInfo | None = None
            if len(previous_prices) > 0:
                previous_price = previous_prices[-1]
                historical_low_price = min(previous_prices, key=lambda item: item.price)

            # Update database
            product_database.add_price_for_product(product_id,
                                                   lowest_price_info_found.price,
                                                   lowest_price_info_found.source_link,
                                                   lowest_price_info_found.date)

            product_name = product_database.get_product_name(product_id)
            # Send notifications
            notify_of_current_lowest_price(product_name, lowest_price_info_found, previous_price, historical_low_price)
        rest_time = random.randint(30, 600)
        logging.debug(f"Waiting {rest_time} seconds before scraping for new product")


if __name__ == "__main__":
    logging.basicConfig(level=config_manager.logging_level)
    logging.info("Scraping started")
    random.seed()
    while True:
        scrape_sites()
        if config_manager.scrape_interval > 0:
            logging.info(f"Waiting {(config_manager.scrape_interval / 60.0):.2f} minutes before scraping again")
            time.sleep(config_manager.scrape_interval)
        else:
            random_time_to_sleep = random.randint(300, 1800)
            logging.info(f"Waiting {(random_time_to_sleep / 60.0):.2f} minutes before scraping again")
            time.sleep(random_time_to_sleep)
