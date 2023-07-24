import json
import logging


CONFIG_FILE_PATH = "config.json"
SCRAPER_INTERVAL_KEY = "scraper-interval"
LOGGING_LEVEL_KEY = "logging-level"


class Config:
    scrape_interval: int
    logging_level: int
    
    def __init__(self, config_path=CONFIG_FILE_PATH):
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
        with open(CONFIG_FILE_PATH, "w") as json_file:
            self.raw_json[SCRAPER_INTERVAL_KEY] = self.scrape_interval
            self.raw_json[LOGGING_LEVEL_KEY] = self.logging_level

            json.dump(self.raw_json, json_file)


if __name__ == "__main__":
    c = Config()
    pass
