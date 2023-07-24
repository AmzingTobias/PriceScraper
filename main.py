import logging
from database_manager import DatabaseManager
from config.config import Config
import time

if __name__ == "__main__":
    config_manager = Config("config/config.json")
    logging.basicConfig(level=logging.INFO)
    logging.info("Scraping started")
    while True:
        db = DatabaseManager()
        db.scrape_sites()
        logging.info(f"Waiting {config_manager.scrape_interval / 60.0} minutes before scraping again")
        time.sleep(config_manager.scrape_interval)
