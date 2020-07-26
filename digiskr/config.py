import importlib.util
import os
import logging
import json

class ConfigNotFoundException(Exception):
    pass


class ConfigError(object):
    def __init__(self, key, message):
        self.key = key
        self.message = message

    def __str__(self):
        return "Configuration Error (key: {0}): {1}".format(self.key, self.message)


class Config:
    instance = None

    @staticmethod
    def _loadPythonFile(file):
        spec = importlib.util.spec_from_file_location("settings", file)
        cfg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cfg)
        conf = {}
        for name, value in cfg.__dict__.items():
            if name.startswith("__"):
                continue
            conf[name] = value
        return conf

    @staticmethod
    def _loadJsonFile(file):
        with open(file, "r") as f:
            conf = {}
            for k, v in json.load(f).items():
                conf[k] = v
            return conf

    @staticmethod
    def _loadConfig():
        for file in ["./settings.json", "./config.py"]:
            try:
                if file.endswith(".py"):
                    return Config._loadPythonFile(file)
                elif file.endswith(".json"):
                    return Config._loadJsonFile(file)
                else:
                    logging.warning("unsupported file type: %s", file)
            except FileNotFoundError:
                pass
        raise ConfigNotFoundException(
            "no usable config found! please make sure you have a valid configuration file!")

    @staticmethod
    def get():
        if Config.instance is None:
            Config.instance = Config._loadConfig()
        return Config.instance

    @staticmethod
    def store():
        with open("settings.json", "w") as file:
            json.dump(Config.get().__dict__(), file, indent=4)

    @staticmethod
    def validateConfig():
        conf = Config.get()
        errors = [
            Config.checkTempDirectory(conf)
        ]

        return [e for e in errors if e is not None]

    @staticmethod
    def checkTempDirectory(conf: dict):
        key = "PATH"
        if key not in conf or conf[key] is None:
            return ConfigError(key, "temporary directory is not set")
        if not os.path.exists(conf[key]):
            return ConfigError(key, "temporary directory doesn't exist")
        if not os.path.isdir(conf[key]):
            return ConfigError(key, "temporary directory path is not a directory")
        if not os.access(conf[key], os.W_OK):
            return ConfigError(key, "temporary directory is not writable")
        return None