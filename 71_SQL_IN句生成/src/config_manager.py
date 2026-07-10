import yaml
import os

class ConfigManager:
    def __init__(self, config_path="config/main.yaml"):
        self.config_path = config_path

    def load_config(self):
        if not os.path.exists(self.config_path):
            return {}
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
