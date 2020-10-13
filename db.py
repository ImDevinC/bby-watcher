import logging
import sqlite3
from sqlite3 import Error
from typing import List

from yoyo import read_migrations
from yoyo import get_backend


from bbyproduct import BBYProduct

TABLE_NAME = 'products'


class Database:
    def __init__(self, path):
        self.path = path
        self.connection = None

    def _connect(self):
        self.connection = sqlite3.connect(self.path)

    def do_migrations(self, migration_path):
        logging.debug(self.path)
        backend = get_backend('sqlite:///{}'.format(self.path))
        migrations = read_migrations(migration_path)
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))

    def _get_rows(self, query):
        if self.connection is None:
            self._connect()
        cur = self.connection.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return rows

    def _execute_query(self, query):
        if self.connection is None:
            self._connect()
        cur = self.connection.cursor()
        cur.execute(query)
        self.connection.commit()

    def _execute_query_list(self, queries):
        if self.connection is None:
            self._connect()
        cur = self.connection.cursor()
        for query in queries:
            logging.debug(query)
            cur.execute(query)
        self.connection.commit()

    def get_path(self):
        rows = self._get_rows('PRAGMA database_list;')
        for row in rows:
            print(row[0], row[1], row[2])

    def show_tables(self):
        rows = self._get_rows(
            'SELECT name FROM sqlite_master WHERE type = \'table\' AND name NOT LIKE \'sqlite_%\';')
        for row in rows:
            logging.debug(row)

    def get_all_items(self):
        return self._get_rows('SELECT sku, inStock from {table};'.format(table=TABLE_NAME))

    def get_duplicate_items(self, skus: List[str]):
        return self._get_rows('SELECT sku, inStock FROM {table} WHERE sku IN ({skus});'.format(table=TABLE_NAME, skus=skus))

    def save_products_to_table(self, products: List[BBYProduct]):
        queries = []
        for product in products:
            if product.needs_update:
                queries.append('UPDATE {table} SET inStock = {inStock} WHERE sku = \'{sku}\';'.format(
                    table=TABLE_NAME, inStock=product.in_stock, sku=product.sku))
            else:
                queries.append('INSERT INTO {table} (sku, inStock) VALUES (\'{sku}\', {in_stock});'.format(
                    table=TABLE_NAME, sku=product.sku, in_stock=product.in_stock))
        if len(queries) == 0:
            return
        self._execute_query_list(queries)

    def update_product(self, product: BBYProduct, new: bool = False):
        if new:
            query = 'INSERT INTO {table} (sku, inStock) VALUES (\'{sku}\', {in_stock});'.format(
                table=TABLE_NAME, sku=product.sku, in_stock=product.in_stock)
        else:
            query = 'UPDATE {table} SET inStock = {inStock} WHERE sku = \'{sku}\';'.format(
                table=TABLE_NAME, inStock=product.in_stock, sku=product.sku)
        self._execute_query(query)
