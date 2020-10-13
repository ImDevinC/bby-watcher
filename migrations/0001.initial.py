from yoyo import step
steps = [
    step('CREATE TABLE products (id integer primary key asc, sku text, inStock int)',
         'DROP TABLE products')
]
