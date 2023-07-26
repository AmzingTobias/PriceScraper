import logging
import time

from config.config import Config
from database.product_database_manager import ProductDatabaseManager

if __name__ == "__main__":
    config_manager = Config("config/config.json")
    logging.basicConfig(level=logging.INFO)
    logging.info("Scraping started")
    while True:
        db = ProductDatabaseManager("database/")
        db.scrape_sites()
        logging.info(f"Waiting {config_manager.scrape_interval / 60.0} minutes before scraping again")
        time.sleep(config_manager.scrape_interval)
