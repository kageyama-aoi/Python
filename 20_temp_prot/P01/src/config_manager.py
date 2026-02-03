import os

from src.utils.errors import UserInputError


DEFAULT_CONFIG = {
    "app": {"name": "data-flow-portal", "version": "0.1.0"},
    "paths": {
        "input_csv": "data/input/data_flow_dummy.csv",
        "output_dir": "data/output/portal",
        "assets_dir": "data/output/portal/assets",
        "log_dir": "logs",
    },
    "csv": {
        "required_columns": ["event_id", "attr_type"],
        "optional_columns": [
            "table",
            "operation",
            "trigger",
            "before",
            "after",
            "note",
            "sql",
        ],
        "carry_forward_columns": ["table", "operation", "trigger", "sql"],
        "null_values": ["NULL", "null", "None", ""],
    },
    "display": {
        "fixed_columns": ["event_id", "table", "operation", "trigger"],
        "priority_columns": [],
        "show_generated_at": True,
        "show_input_name": True,
        "show_legend": True,
    },
}


class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path

    def load(self):
        data = self._load_yaml(self.config_path)
        merged = deep_merge(DEFAULT_CONFIG, data or {})
        self._validate(merged)
        return merged

    def _load_yaml(self, path):
        if not os.path.exists(path):
            raise UserInputError(f"config not found: {path}")
        try:
            import yaml
        except ImportError as exc:
            raise UserInputError(
                "PyYAML が必要です。pip install -r requirements.txt を実行してください。"
            ) from exc
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _validate(self, config):
        paths = config.get("paths", {})
        csv_conf = config.get("csv", {})
        display = config.get("display", {})

        for key in ("input_csv", "output_dir", "assets_dir", "log_dir"):
            if not paths.get(key):
                raise UserInputError(f"paths.{key} が未設定です。")

        required_columns = csv_conf.get("required_columns", [])
        if "event_id" not in required_columns or "attr_type" not in required_columns:
            raise UserInputError("csv.required_columns に event_id と attr_type が必要です。")

        fixed_columns = display.get("fixed_columns", [])
        if not fixed_columns:
            raise UserInputError("display.fixed_columns が空です。")


def deep_merge(base, incoming):
    if not isinstance(incoming, dict):
        return base
    merged = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
