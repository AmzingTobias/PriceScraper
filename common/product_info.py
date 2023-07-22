

class ProductInfo:
    availability: bool
    price: float

    def __init__(self, price: float, availability: bool):
        self.availability = availability
        self.price = price
