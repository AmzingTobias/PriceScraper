import logging
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
}

STATUS_OK = 200


class Scraper:
    url: str

    def __init__(self, url: str):
        self.url = url


def validate_url(url: str, host_name_required: str) -> bool:
    parser = urlparse(url)
    if parser.hostname == host_name_required:
        return True
    else:
        logging.warning(f"{url} is not valid for {host_name_required}")
        return False


def log_invalid_request(request_code: int) -> None:
    logging.warning(f"Request failed with code: {request_code}")


def log_url_request(url: str) -> None:
    logging.info(f"Using link {url} to get product info")


def log_price_found_from_request(price: float) -> None:
    logging.info(f"Price found: £{price}")


def log_product_availability_from_request(in_stock: bool) -> None:
    if in_stock:
        logging.info("Product in stock")
    else:
        logging.info("Product out of stock")


def log_price_invalid() -> None:
    logging.error("Price found was invalid")
