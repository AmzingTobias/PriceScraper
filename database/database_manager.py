import datetime
import logging
import sqlite3

DATABASE_NAME = "data.db"
DATABASE_SQL_CREATE_FILE = "data.sql"


class DatabaseManager:
    """
    Parent class for all database managers
    Attributes:
        conn (sqlite3.Connection): The connection to the database
    """
    conn: sqlite3.Connection

    def __init__(self, database_folder_path: str):
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
        Create tables in the database if needed, using the sql file that is found in the same path
        :param database_folder_path: The folder location of the database files, should end with a slash
        """
        cursor: sqlite3.Cursor = self.conn.cursor()
        try:
            with open(database_folder_path + DATABASE_SQL_CREATE_FILE, "r") as sql_file:
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

    def __del__(self):
        logging.info("Closing connection to database")
        self.conn.close()
