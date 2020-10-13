# from dataclasses import dataclass, field, InitVar
import logging
import os
import json
import time

import requests

from bbyproduct import BBYProduct
from db import Database

API_KEY = os.environ['API_KEY']
WEBHOOK_URL = os.environ['WEBHOOK_URL']
SLEEP_TIME = int(os.environ['SLEEP_TIME'])

ROOT_URL = 'https://api.bestbuy.com/v1/products({query})'
SHOW_RESULTS = 'sku,name,regularPrice,orderable,addToCartUrl,thumbnailImage'

logging.basicConfig(level=logging.DEBUG)


def send_to_discord(product: BBYProduct):
    message = {
        'embeds': [
            {
                'color': '6799926',
                'tile': 'Card is in stock!',
                'fields': [
                    {
                        'name': 'Card',
                        'value': product.name
                    },
                    {
                        'name': 'Price',
                        'value': '${:.2f}'.format(product.price)
                    },
                    {
                        'name': 'URL',
                        'value': 'https://www.bestbuy.com/site/{sku}.p?skuId={sku}'.format(sku=product.sku)
                    }
                ],
                'thumbnail': {
                    'url': product.image
                }
            }
        ]
    }
    try:
        resp = requests.post(WEBHOOK_URL, json=message)
    except Exception as ex:
        logging.error(ex)
        return
    if resp.status_code == 429:
        time.sleep(10)
        send_to_discord(product)


def get_product_info(query: str):
    params = {
        'show': SHOW_RESULTS,
        'format': 'json',
        'apiKey': API_KEY
    }
    response = requests.get(ROOT_URL.format(query=query), params=params)
    return response.json().get('products', [])


def main(database: Database):
    query = os.getenv('QUERY')
    if not query:
        raise ValueError(
            'QUERY environment variable is missing. See https://bestbuyapis.github.io/api-documentation for more information.')

    existing_products = database.get_all_items()
    product_mapping = {x[0]: x[1] == 1 for x in existing_products}

    products = get_product_info(query)
    if not products:
        logging.error('No products found')
        return

    product_list = [BBYProduct(x) for x in products]

    for product in product_list:
        if product.in_stock and not product_mapping.get(product.sku):
            logging.info(
                '{sku} was not in stock, now is'.format(sku=product.sku))
            send_to_discord(product)
            database.update_product(product)
        elif not product.in_stock and product_mapping.get(product.sku):
            logging.info(
                '{sku} was in stock, now isn\'t'.format(sku=product.sku))
            database.update_product(product)
        elif product.sku not in product_mapping:
            logging.info(
                'New product {sku}, add to database'.format(sku=product.sku))
            database.update_product(product, new=True)


def configure_database():
    database = Database('/data/db.sqlite')
    database.do_migrations(os.path.dirname(
        os.path.abspath(__file__)) + '/migrations')
    return database


if __name__ == '__main__':
    database = configure_database()
    while True:
        main(database)
        time.sleep(SLEEP_TIME)
