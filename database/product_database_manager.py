import datetime
import logging
import sqlite3

from common.product_info import PriceInfo, date_to_string, string_to_date

DATABASE_NAME = "products.db"
PRODUCTS_TABLE_NAME = "Products"
SOURCES_TABLE_NAME = "Sources"
PRICES_TABLE_NAME = "Prices"


class ProductDatabaseManager:
    """
    The Database manager for products that handles making requests to the SQL database
    Attributes:
        conn (sqlite3.Connection): The connection to the database
    """
    conn: sqlite3.Connection

    def __init__(self, database_folder_path: str = ""):
        """
        :param database_folder_path: The folder location of the database files, should end with a slash
        """
        # Connect to the database
        self.conn = sqlite3.connect(database_folder_path + DATABASE_NAME)
        # Ensure foreign key checks exist
        self.conn.execute('PRAGMA foreign_keys = ON')
        logging.info(f"Connection established to {database_folder_path + DATABASE_NAME}")
        self.create_tables(database_folder_path)

    def create_tables(self, database_folder_path):
        """
        Create tables in the database if needed, using the "products.sql" file that is found in the same path
        :param database_folder_path: The folder location of the database files, should end with a slash
        """
        cursor: sqlite3.Cursor = self.conn.cursor()
        try:
            with open(database_folder_path + "products.sql", "r") as sql_file:
                sql_commands = sql_file.read()
                try:
                    logging.info("Creating database tables if needed")
                    # Will only create the tables if needed
                    cursor.executescript(sql_commands)
                    cursor.close()
                except sqlite3.Error as sqlite_error:
                    logging.critical(f"Error executing sql command: {sqlite_error}")
                    self.__del__()
                    raise SystemExit(f"Error executing sql command: {sqlite_error}")
        except FileNotFoundError as file_open_error:
            logging.critical(f"Error executing sql command, file does not exist")
            self.__del__()
            raise SystemExit(f"{file_open_error}")

    def get_product_name(self, product_id: int) -> str | None:
        """
        Get a products name from the database, using the products id
        :param product_id: The ID of the product to get the name for
        """
        cur = self.conn.cursor()
        cur.execute(f"SELECT Name FROM {PRODUCTS_TABLE_NAME} WHERE Id = ?", (product_id,))
        result = cur.fetchone()
        if len(result) > 0:
            cur.close()
            return result[0]
        else:
            cur.close()
            return None

    def add_product(self, product_name: str) -> bool:
        """
        Add a product into the database
        :param product_name: The product name to add to the database
        :return: True if the product is added to the database, False if not
        """
        data_added = True
        logging.info(f"Attempting to add {product_name} to the database")
        cur = self.conn.cursor()
        sql_command = f"INSERT INTO {PRODUCTS_TABLE_NAME} (Name) VALUES (?);"
        try:
            cur.execute(sql_command, (product_name,))
        except sqlite3.IntegrityError:
            logging.warning(f"{product_name} already exists in database")
            data_added = False
        cur.close()
        try:
            self.conn.commit()
        except sqlite3.OperationalError as operation_error:
            # Most likely the database is locked
            logging.warning(f"Could not commit to database: {operation_error}")
            data_added = False
        return data_added

    def add_product_sources(self, product_id: int, product_sources: list[str]) -> bool:
        """
        Add sources for a given product, that can be scraped to get price information
        :param product_id: The product id to add the source for
        :param product_sources: A list of different product sources to add
        :return: True if the product sources are added, False otherwise
        """
        cur = self.conn.cursor()
        values = [(product_id, source) for source in product_sources]
        values_added = True
        try:
            logging.info(f"Adding {product_sources} to product ID: {product_id}")
            # Allows a list of values to be used
            cur.executemany(f"INSERT INTO {SOURCES_TABLE_NAME} (Product_Id, Site_link) VALUES (?, ?)", values)
        except sqlite3.IntegrityError:
            logging.warning(f"{product_id} source(s) already exists: {product_sources}")
            values_added = False
        cur.close()
        try:
            self.conn.commit()
        except sqlite3.OperationalError as operation_error:
            # Most likely the database is locked
            logging.warning(f"Could not commit to database: {operation_error}")
            values_added = False
        return values_added

    def get_product_id(self, product_name) -> int | None:
        """
        Get a product ID, using a product name
        :param product_name: The product name
        :return: The ID of the product in the database, or None if the product does not exist
        """
        cur = self.conn.cursor()
        cur.execute(f"SELECT Id FROM {PRODUCTS_TABLE_NAME} WHERE Name=(?)", (product_name,))
        id_found = cur.fetchone()
        cur.close()
        if id_found is not None:
            if len(id_found) > 0:
                logging.info(f"{product_name} Id is: {id_found[0]}")
                return id_found[0]
        logging.warning(f"{product_name} does not exist in database")
        return None

    def get_all_product_ids(self) -> list[int]:
        """
        Get all product ID's that exist in the database
        :return: A list of product ID's
        """
        logging.info("Getting all product ID's from database")
        cur = self.conn.cursor()
        cur.execute(f"SELECT Id FROM {PRODUCTS_TABLE_NAME}")
        all_ids = cur.fetchall()
        cur.close()
        if all_ids is not None:
            return [product_id[0] for product_id in all_ids]
        else:
            logging.info("No products exist in database")
            return []

    def get_all_source_sites(self, product_id) -> list[{id, str}]:
        """
        Get all source sites for a product
        :param product_id: The ID of the product to get the source sites for
        :return: A list of sets in the format {source_id, source_link}
        """
        cur = self.conn.cursor()
        cur.execute(f"SELECT Id, Site_link FROM {SOURCES_TABLE_NAME} WHERE Product_Id=(?)", (product_id,))
        data = cur.fetchall()
        cur.close()
        if data is not None:
            return data
        else:
            return []

    def get_prices_for_product(self, product_id: int) -> list[PriceInfo]:
        """
        Get a history of all prices for a product
        :param product_id: The product id to get the price history for
        :return: A list of all prices for the product, sorted by date
        """
        cur = self.conn.cursor()
        sql_statement = f"SELECT {PRICES_TABLE_NAME}.Price, {SOURCES_TABLE_NAME}.Site_Link, {PRICES_TABLE_NAME}.Date " \
                        f"FROM {PRICES_TABLE_NAME} " \
                        f"LEFT JOIN {SOURCES_TABLE_NAME} ON {PRICES_TABLE_NAME}.Site_Id = {SOURCES_TABLE_NAME}.Id " \
                        f"WHERE {PRICES_TABLE_NAME}.Product_Id = ?"
        cur.execute(sql_statement, (product_id,))
        price_data = cur.fetchall()
        cur.close()
        # Create the PriceInfo objects with the data received
        price_info_converted = [PriceInfo(price[0], price[1], string_to_date(price[2]))
                                for price in price_data]
        # Sort the list of prices by date
        price_info_converted_sorted = sorted(price_info_converted, key=lambda x: x.date)
        logging.info(f"Total prices found for product {product_id}: {len(price_info_converted_sorted)}")
        return price_info_converted_sorted

    def get_price_for_product_with_date(self, product_id: int, date_for_search: datetime.date) -> PriceInfo | None:
        """
        Get the price for a product using a date
        :param product_id: The product to get the price for
        :param date_for_search: The date to get the price at
        :return: The PriceInfo found from the database, or None if no price exists
        """
        # Convert the date into a string for database lookup
        date_string_for_lookup = date_to_string(date_for_search)
        cur = self.conn.cursor()
        sql_statement = f"SELECT {PRICES_TABLE_NAME}.Price, {SOURCES_TABLE_NAME}.Site_Link, {PRICES_TABLE_NAME}.Date " \
                        f"FROM {PRICES_TABLE_NAME} " \
                        f"LEFT JOIN {SOURCES_TABLE_NAME} ON {PRICES_TABLE_NAME}.Site_Id = {SOURCES_TABLE_NAME}.Id " \
                        f"WHERE {PRICES_TABLE_NAME}.Product_Id = ? AND {PRICES_TABLE_NAME}.Date = ?"
        cur.execute(sql_statement, (product_id, date_string_for_lookup,))
        price_data = cur.fetchone()
        cur.close()
        if price_data is not None:
            return PriceInfo(price_data[0], price_data[1], string_to_date(price_data[2]))
        else:
            return None

    def add_price_for_product(self, product_id: int, price: float, source_url: str,
                              date: datetime.date = datetime.date.today()) -> bool:
        """
        Add a price to the database for a given product
        :param product_id: The product id to add the price for
        :param price: The price to add / update the database
        :param source_url: The Source link that was used to find the price
        :param date: The date the price was obtained, by default it will use today's date
        :return: True if the price is added or updated in the database, False otherwise
        """
        cur = self.conn.cursor()
        date_string_for_lookup = date_to_string(date)
        sql_update_statement = f"UPDATE {PRICES_TABLE_NAME} " \
                               f"SET Price = ?, Site_Id = " \
                               f"(SELECT {SOURCES_TABLE_NAME}.Id FROM {SOURCES_TABLE_NAME} " \
                               f"WHERE {SOURCES_TABLE_NAME}.Site_link = ? AND {SOURCES_TABLE_NAME}.Product_Id = ?) " \
                               f"WHERE Product_Id = ? AND Date = ?"
        cur.execute(sql_update_statement, (price, source_url, product_id, product_id, date_string_for_lookup,))
        if cur.rowcount == 0:
            # Needs to be inserted
            sql_insert_statement = f"INSERT INTO {PRICES_TABLE_NAME} (Product_Id, Date, Price, Site_Id) " \
                                   f"VALUES (?, ?, ?, (" \
                                   f"SELECT {SOURCES_TABLE_NAME}.Id FROM {SOURCES_TABLE_NAME} " \
                                   f"WHERE {SOURCES_TABLE_NAME}.Site_link = ? AND {SOURCES_TABLE_NAME}.Product_Id = ?))"
            try:
                cur.execute(sql_insert_statement, (product_id, date_string_for_lookup, price, source_url, product_id,))
            except sqlite3.IntegrityError as insert_error:
                logging.warning(f"Insert error to database: {insert_error}")
                cur.close()
                return False
            try:
                self.conn.commit()
                if cur.rowcount > 0:
                    cur.close()
                    return True
                else:
                    cur.close()
                    return False
            except sqlite3.OperationalError as operation_error:
                logging.warning(f"Could not commit to database: {operation_error}")
                cur.close()
                return False
        else:
            try:
                self.conn.commit()
                cur.close()
                return True
            except sqlite3.OperationalError as operation_error:
                logging.warning(f"Could not commit to database: {operation_error}")
                cur.close()
                return False

    def __del__(self):
        logging.info("Closing connection to database")
        self.conn.close()


if __name__ == '__main__':
    print(f"{ProductDatabaseManager.__name__}:\n{ProductDatabaseManager.__doc__}")
    for name, method in ProductDatabaseManager.__dict__.items():
        if callable(method) and hasattr(method, '__doc__'):
            docstring = method.__doc__
            if docstring:
                print(f"Method '{name}':\n{docstring.strip()}\n")
