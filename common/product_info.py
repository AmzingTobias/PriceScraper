import datetime


class ProductInfo:
    availability: bool
    price: float

    def __init__(self, price: float, availability: bool):
        self.availability = availability
        self.price = price


class PriceInfo:
    price: float | None
    source_link: str | None
    date: datetime.date | None

    def __init__(self, price: float | None, source_link: str | None, date: datetime.date | None):
        self.price = price
        self.source_link = source_link
        self.date = date


def date_to_string(date: datetime.date) -> str:
    return date.strftime("%d-%m-%Y")


def string_to_date(date_as_string: str) -> datetime.date:
    return datetime.datetime.strptime(date_as_string, "%d-%m-%Y").date()


def get_price_difference_string(new_price: float, old_price: float) -> str:
    try:
        percentage_price_difference = ((old_price - new_price) / old_price) * 100.0
    except ZeroDivisionError:
        percentage_price_difference = 100.0
    if new_price >= old_price:
        return f"+{(percentage_price_difference * -1.0):.2f}%"
    else:
        return f"-{percentage_price_difference:.2f}%"
