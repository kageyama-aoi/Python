import argparse
import os
import sys
import webbrowser

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.config_manager import ConfigManager
from src.handlers.column_planner import plan_columns
from src.handlers.context_filler import fill_context
from src.handlers.csv_loader import load_csv
from src.handlers.event_aggregator import aggregate_events
from src.handlers.portal_renderer import PortalRenderer
from src.utils.errors import UserInputError
from src.utils.log import setup_logger


def parse_args():
    parser = argparse.ArgumentParser(description="Data Flow Portal")
    parser.add_argument("--config", default="config/main.yaml")
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--open", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        config = ConfigManager(args.config).load()
        if args.input:
            config["paths"]["input_csv"] = args.input
        if args.output:
            config["paths"]["output_dir"] = args.output
            config["paths"]["assets_dir"] = os.path.join(args.output, "assets")

        logger = setup_logger(config["paths"]["log_dir"])
        logger.info("start rendering portal")
        logger.info("input_csv=%s", config["paths"]["input_csv"])
        logger.info("output_dir=%s", config["paths"]["output_dir"])

        rows = load_csv(
            config["paths"]["input_csv"],
            config["csv"]["required_columns"],
        )
        filled_rows = fill_context(
            rows,
            config["csv"]["carry_forward_columns"],
            config["csv"]["required_columns"],
        )
        events = aggregate_events(filled_rows, config["csv"]["null_values"])
        columns = plan_columns(
            filled_rows,
            config["display"].get("priority_columns", []),
        )

        renderer = PortalRenderer(config)
        index_path = renderer.render(events, columns, config["paths"]["input_csv"])

        logger.info("generated: %s", index_path)
        if args.open:
            webbrowser.open(f"file:///{os.path.abspath(index_path)}")
    except UserInputError as exc:
        print(f"[INPUT ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
