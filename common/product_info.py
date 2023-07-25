import datetime


class ProductInfo:
    """
    Contains basic information for a product

    Attributes:
        availability (bool): True if the product is available, False otherwise
        price (float): The price of the product
    """
    availability: bool
    price: float

    def __init__(self, price: float, availability: bool) -> None:
        """
        Initialize product info
        :param price: The price of the product
        :param availability: True if the product is available, false otherwise
        """
        self.availability = availability
        self.price = price


class PriceInfo:
    """
    Contains basic information for a product

    Attributes:
        price (float | None): The price of the product, or None
        source_link (str | None): The source url the price was found at, or None
        date (datetime.date | None): The date the product's price was found, or None
    """
    price: float | None
    source_link: str | None
    date: datetime.date | None

    def __init__(self, price: float | None, source_link: str | None, date: datetime.date | None):
        """
        Initialize price info
        :param price:  The price of the product
        :param source_link: The URL the price was found at
        :param date: The date the price was found
        """
        self.price = price
        self.source_link = source_link
        self.date = date


DATE_STRING_FORMAT = "%d-%m-%Y"


def date_to_string(date: datetime.date) -> str:
    """
    Convert a date into a string
    :param date: The date object to convert into a string
    :return: The date converted as a string in the format found in DATE_DATE_STRING_FORMAT
    """
    return date.strftime(DATE_STRING_FORMAT)


def string_to_date(date_as_string: str) -> datetime.date:
    """
    Convert a string into a date object
    :param date_as_string: A string in the format DATE_STRING_FORMAT
    :return: The date object representation of the string
    """
    return datetime.datetime.strptime(date_as_string, DATE_STRING_FORMAT).date()


def get_price_difference_string(new_price: float, old_price: float) -> str:
    """
    Create a string that represents the percentage difference between two numbers, including a + and - as appropriate.
    Formatted to 2 decimal places
    :param new_price: The new price
    :param old_price: The old price
    :return: The string representation of the percentage difference
    """
    try:
        percentage_price_difference = ((old_price - new_price) / old_price) * 100.0
    except ZeroDivisionError:
        percentage_price_difference = 100.0
    if new_price >= old_price:
        return f"+{(percentage_price_difference * -1.0):.2f}%"
    else:
        return f"-{percentage_price_difference:.2f}%"
