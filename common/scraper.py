import logging
from urllib.parse import urlparse

# Default headers to use when scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
}


class Scraper:
    """
    Base Scraper class

    Attributes:
        url (str): The URL that will be scraped
    """
    url: str

    def __init__(self, url: str):
        """
        :param url: The URL to scrape
        """
        self.url = url


def validate_url(url: str, host_name_required: str) -> bool:
    """
    Validates the supplied URL contains the host name supplied
    :param url: The URL to check
    :param host_name_required: The host name the URL must contain
    :return: True if the URL contains the host name, False otherwise
    """
    # Parse the URL to get the host name from it
    parser = urlparse(url)
    if parser.hostname == host_name_required:
        return True
    else:
        logging.debug(f"{url} is not valid for {host_name_required}")
        return False


def log_invalid_request(request_code: int) -> None:
    """
    Log an invalid request
    :param request_code: The request code that was received when the request failed
    """
    logging.error(f"Request failed with code: {request_code}")


def log_url_request(url: str) -> None:
    """
    Log that a URL is being requested
    :param url: The URL that is being requested
    """
    logging.info(f"Using link {url} to get product info")


def log_price_found_from_request(price: float) -> None:
    """
    Log the price that was found from a request
    :param price: The price found from a request
    """
    logging.info(f"Price found: £{price}")


def log_product_availability_from_request(in_stock: bool) -> None:
    """
    Log if the product is available or not
    :param in_stock: True if the product is available, False otherwise
    """
    if in_stock:
        logging.info("Product in stock")
    else:
        logging.info("Product out of stock")


def log_price_invalid() -> None:
    """
    Log if an error occurred that meant the price was not valid
    """
    logging.error("Price found was invalid")
