import os
import re
import sys
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config_manager import ConfigManager
from src.handlers.column_planner import plan_columns
from src.handlers.context_filler import fill_context
from src.handlers.csv_loader import load_csv
from src.handlers.event_aggregator import aggregate_events
from src.handlers.portal_renderer import PortalRenderer


class TestTableGrouping(unittest.TestCase):
    def test_table_groups_are_contiguous(self):
        config = ConfigManager(os.path.join(ROOT_DIR, "config", "main.yaml")).load()
        config["paths"]["input_csv"] = os.path.join(
            ROOT_DIR, "data", "input", "data_flow_dummy_alt.csv"
        )

        rows = load_csv(
            config["paths"]["input_csv"],
            config["csv"]["required_columns"],
        )
        filled = fill_context(
            rows,
            config["csv"]["carry_forward_columns"],
            config["csv"]["required_columns"],
        )
        events = aggregate_events(filled)
        columns = plan_columns(filled, config["display"].get("priority_columns", []))

        renderer = PortalRenderer(config)
        html = renderer._build_html(events, columns, config["paths"]["input_csv"], "assets/style.css")

        thead_match = re.search(r"<thead>(.*?)</thead>", html, re.DOTALL)
        self.assertIsNotNone(thead_match, "thead not found in HTML")
        rows_html = re.findall(r"<tr>(.*?)</tr>", thead_match.group(1), re.DOTALL)
        self.assertGreaterEqual(len(rows_html), 2, "header rows not found")

        table_group_row = rows_html[1]
        labels = re.findall(r"<th[^>]*>(.*?)</th>", table_group_row, re.DOTALL)
        labels = [re.sub(r"<.*?>", "", label).strip() for label in labels]
        labels = [label for label in labels if label]

        expected_order = ["products", "shipments", "subscriptions"]
        self.assertEqual(labels, expected_order)
        self.assertEqual(len(labels), len(set(labels)), "table group labels are repeated")


if __name__ == "__main__":
    unittest.main()
