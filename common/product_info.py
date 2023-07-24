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
