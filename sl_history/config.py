import os
import platform
import shutil
import pymel.core as pm
from sl_history import fileFn


class Config:

    DEFAULT_CONFIG_PATH = os.path.join(pm.moduleInfo(mn="sl_history", p=1), "sl_history", "config", "default_config.json")  # type: str
    CONFIG_PATH = os.path.join(pm.moduleInfo(mn="sl_history", p=1), "sl_history", "config", "config.json")  # type: str

    @classmethod
    def load(cls):
        return fileFn.load_json(cls._get_config_file())

    @classmethod
    def update(cls, new_config_dict):
        current_config = cls.load()  # type: dict
        current_config.update(new_config_dict)
        fileFn.write_json(cls._get_config_file(), current_config)

    @classmethod
    def get(cls, key, default=None):
        current_config = cls.load()  # type:dict
        if key not in current_config.keys():
            current_config[key] = default
            cls.update(current_config)
        return current_config.get(key)

    @classmethod
    def set(cls, key, value):
        cls.update({key: value})

    @classmethod
    def reset(cls):
        shutil.copy2(Config.DEFAULT_CONFIG_PATH, Config.CONFIG_PATH)

    @classmethod
    def toggle_var(cls, var, state):
        cls.set(var, state)

    @staticmethod
    def _get_config_file():
        if not os.path.isfile(Config.CONFIG_PATH):
            shutil.copy2(Config.DEFAULT_CONFIG_PATH, Config.CONFIG_PATH)

        return Config.CONFIG_PATH


if __name__ == "__main__":
    pass
