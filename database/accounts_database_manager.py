import sqlite3

from database.database_manager import DatabaseManager

USERS_TABLE = "Users"
NOTIFICATIONS_TABLE = "Notifications"
DISCORD_NOTIFICATION_TABLE = "Discord_webhooks"
PRODUCT_NOTIFICATIONS_TABLE = "Product_notifications"


class NotificationSettings:
    """
    Holds notification settings for a user
    Attributes:
        user_id (int): The Id of the user the notification settings are for
        enabled (bool): True if the user wants to receive notifications, False otherwise
        no_price_change_enabled (bool): True if the user wants to receive notifications when the price hasn't changed,
        False otherwise
    """
    user_id: int
    enabled: bool
    no_price_change_enabled: bool

    def __init__(self, user_id: int, enabled: bool, no_price_change_enabled: bool):
        self.user_id = user_id
        self.enabled = enabled
        self.no_price_change_enabled = no_price_change_enabled


class AccountDatabaseManager(DatabaseManager):
    """
    The Database manager for accounts, handles making requests to the SQL database
    Attributes:
        conn (sqlite3.Connection): The connection to the database
    """
    conn: sqlite3.Connection

    def __init__(self, database_folder_path: str = ""):
        """
        :param database_folder_path: The folder location of the database files, should end with a slash
        """
        super().__init__(database_folder_path)

    def get_users_for_notifications_of_product(self, product_id: int, price_changed=True) -> list[NotificationSettings]:
        cur = self.conn.cursor()
        sql_statement = f"SELECT {NOTIFICATIONS_TABLE}.User_Id, {NOTIFICATIONS_TABLE}.Enabled, " \
                        f"{NOTIFICATIONS_TABLE}.No_price_change_enabled " \
                        f"FROM {NOTIFICATIONS_TABLE} " \
                        f"INNER JOIN {PRODUCT_NOTIFICATIONS_TABLE} ON " \
                        f"{NOTIFICATIONS_TABLE}.User_Id = {PRODUCT_NOTIFICATIONS_TABLE}.User_Id " \
                        f"WHERE {PRODUCT_NOTIFICATIONS_TABLE}.Product_Id = ?"
        if not price_changed:
            sql_statement += F" AND {NOTIFICATIONS_TABLE}.No_price_change_enabled = 1"
        cur.execute(sql_statement, (product_id,))
        result = cur.fetchall()
        cur.close()
        if len(result) > 0:
            return [NotificationSettings(entry[0], entry[1] > 0, entry[2] > 0) for entry in result]
        else:
            return []

    def get_discord_webhooks_for_user(self, user_id: int) -> str | None:
        cur = self.conn.cursor()
        sql_statement = f"SELECT Discord_webhook FROM {DISCORD_NOTIFICATION_TABLE} WHERE User_Id = ?"
        cur.execute(sql_statement, (user_id,))
        result = cur.fetchone()
        if len(result) > 0:
            return result[0]
        else:
            return None
