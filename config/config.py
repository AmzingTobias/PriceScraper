import json
import logging

CONFIG_FILE_PATH = "config.json"
SCRAPER_INTERVAL_KEY = "scraper-interval"
LOGGING_LEVEL_KEY = "logging-level"


class Config:
    """
    Loads in a config file and stores the values found as attributes

    Attributes:
        scrape_interval (int): The amount of time in seconds that should take place between each scrape
        logging_level (int): The logging level to use
        config_filepath (str): The filepath to the config
    """
    scrape_interval: int
    logging_level: int
    config_filepath: str

    def __init__(self, config_path=CONFIG_FILE_PATH):
        """
        :param config_path: The path to the config file
        """

        self.config_filepath = config_path

        # Default values for the config file
        self.scrape_interval = 0
        self.logging_level = logging.WARNING
        self.raw_json = dict()

        try:
            with open(config_path, "r") as json_file:
                self.raw_json = json.load(json_file)
        except FileNotFoundError:
            self.create_config_file()

        # Check what values exist from the config file and if they can be loaded in
        if SCRAPER_INTERVAL_KEY in self.raw_json:
            self.scrape_interval = self.raw_json[SCRAPER_INTERVAL_KEY]

        if LOGGING_LEVEL_KEY in self.raw_json:
            self.logging_level = self.raw_json[LOGGING_LEVEL_KEY]

    def create_config_file(self) -> None:
        """
        Creates the config file with the default values
        """
        with open(self.config_filepath, "w") as json_file:
            # Create the config file with the default values
            self.raw_json[SCRAPER_INTERVAL_KEY] = self.scrape_interval
            self.raw_json[LOGGING_LEVEL_KEY] = self.logging_level

            json.dump(self.raw_json, json_file)


if __name__ == "__main__":
    print(Config.__doc__)
    for name, method in Config.__dict__.items():
        if callable(method) and hasattr(method, '__doc__'):
            docstring = method.__doc__
            if docstring:
                print(f"Method '{name}':\n{docstring.strip()}\n")
