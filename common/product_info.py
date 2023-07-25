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

