import os
import yaml
import json
import toml
import logging
from enum import Enum
from typing import Any

class ConfigKey(Enum):
    CACHE_DIR = "cache_dir"

class Configuration:
    def __init__(self, config: str = 'init_config.yml'):
        self.config: dict = {}
        try:
            if os.path.isfile(config):
                with open(config, "r") as stream:
                    if config.endswith(".yaml") or config.endswith(".yml"):
                        self.config = yaml.safe_load(stream)
                    elif config.endswith(".json"):
                        self.config = json.load(stream)
                    elif config.endswith(".toml"):
                        self.config = toml.load(stream)
                    else:
                        raise ValueError(f"Unsupported file format: {config}")
        except FileNotFoundError:
            logging.warning(f"Configuration file '{config}' not found. Using default settings.")
        except (yaml.YAMLError, json.JSONDecodeError, toml.TomlDecodeError) as e:
            logging.error(f"Error parsing {config}: {e}")

    def get_value(self, key: str) -> Any:
        return self.config.get(key)

 