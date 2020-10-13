class BBYProduct(dict):
    def __init__(self, data):
        self.url: str = data.get('addToCartUrl')
        self.name: str = data.get('name')
        self.price: float = float(data.get('regularPrice'))
        self.sku: str = str(data.get('sku'))
        self.in_stock: bool = data.get('orderable') == 'Available'
        self.needs_update: bool = False
        self.image: str = data.get('thumbnailImage')
        dict.__init__(self, url=self.url, name=self.name,
                      price=self.price, sku=self.sku, in_stock=self.in_stock)
