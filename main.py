import logging
import random
import sys
import time

from common.product_info import PriceInfo
from common.scraper import validate_url
from config.config import Config
from database.accounts_database_manager import AccountDatabaseManager
from database.product_database_manager import ProductDatabaseManager
from notifiers.discord import Discord
from scrapers.cdkeys import CDKEYS_HOST_NAME, CDKeys
from scrapers.green_man_gaming import GREEN_MAN_GAMING_HOST_NAME, GreenManGaming

config_path = "config//config.json"
if len(sys.argv) > 1:
    config_path = sys.argv[1]
print(f"Using config file: {config_path}")
config_manager = Config(config_path)


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


def notify_of_current_lowest_price(product_id: int,
                                   product_name: str,
                                   current_lowest_price: PriceInfo,
                                   previous_price_info: PriceInfo,
                                   historical_low_price: PriceInfo,
                                   product_image_url: None | str = None) -> None:
    """
    Notify everyone required of a price change
    :param product_id: The ID of the product, from the database
    :param product_name: THe product name the price change was detected for
    :param current_lowest_price: The current lowest price that was found in the scrape
    :param previous_price_info: The last lowest price that was found in the scrape
    :param historical_low_price: The lowest price that was ever found
    """
    account_database = AccountDatabaseManager(config_manager.database_filepath)
    user_accounts_for_product = []
    if current_lowest_price.price is not None and previous_price_info.price is not None:
        if current_lowest_price.price == previous_price_info.price:
            user_accounts_for_product = account_database.get_users_for_notifications_of_product(product_id, False)
        else:
            user_accounts_for_product = account_database.get_users_for_notifications_of_product(product_id)
    else:
        user_accounts_for_product = account_database.get_users_for_notifications_of_product(product_id)

    discord_webhooks_for_product = [account_database.get_discord_webhooks_for_user(user.user_id)
                                    for user in user_accounts_for_product]

    discord_notifier = Discord(discord_webhooks_for_product)
    discord_notifier.prepare_webhook(product_name,
                                     current_lowest_price,
                                     previous_price_info,
                                     historical_low_price,
                                     product_image_link=product_image_url)
    discord_notifier.send_webhook()


def scrape_sites():
    """
    Scrape all sites for all products that exist in the database, and send out notifications for any price changes that
    are found
    """
    product_database = ProductDatabaseManager(config_manager.database_filepath)
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
            elif validate_url(url, GREEN_MAN_GAMING_HOST_NAME):
                scraper = GreenManGaming(url)
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
            product_image_link = product_database.get_product_image(product_id)
            notify_of_current_lowest_price(product_id, product_name, lowest_price_info_found, previous_price,
                                           historical_low_price, product_image_link)
        rest_time = random.randint(20, 60)
        logging.info(f"Waiting {rest_time} seconds before scraping for new product")
        time.sleep(rest_time)


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
