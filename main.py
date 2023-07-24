import logging
from manager import Manager

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = Manager()
    db.scrape_sites()
