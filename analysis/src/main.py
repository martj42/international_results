#!/usr/bin/env python3
import sys
import os
import argparse
import logging
from pathlib import Path

from statistics_processor import StatisticsProcessor  

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s >> %(levelname)s %(name)s::%(funcName)s: %(message)s'
    )

def find_data_files(root_dir: Path):
    # Finds all CSV files in the root directory
    return list(root_dir.glob("*.csv"))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Extract Watch Data viaa BT")
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for log files"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        required=True,
        help="Directory containing data files"
    )
    return parser.parse_args()


def main():
    """Main application entry point."""
    # Parse command line arguments
    args = parse_arguments()

    # If LOG_LEVEL is set in the environment, override args.log_level
    env_log_level = os.environ.get("LOG_LEVEL")
    if env_log_level:
        args.log_level = env_log_level.upper()

    # Force logging level globally before anything else
    log_level = getattr(logging, args.log_level, logging.INFO)
    logging.basicConfig(level=log_level)

    setup_logging()

    data_dir = Path(args.data_dir).resolve()
    processor = StatisticsProcessor(data_dir)
    processor.process_results()
    processor.print_statistics()


if __name__ == "__main__":
    sys.exit(main())
