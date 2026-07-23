"""Standalone entry point for reopening a tracked Batch Processor project."""

import argparse
import os
import sys


def add_package_root_to_sys_path():
    """Adds the gt-tools package root for direct script execution."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)


def parse_args():
    """Parses launcher arguments.

    Returns:
        argparse.Namespace: Parsed launcher options.
    """
    parser = argparse.ArgumentParser(description="Batch Processor Standalone Launcher")
    parser.add_argument("--project-file", required=True, help="Saved .batch project to open.")
    return parser.parse_args()


def main():
    """Launches an independent Batch Processor for the requested project."""
    add_package_root_to_sys_path()
    args = parse_args()
    from gt.tools import batch_processor

    batch_processor.launch_tool(project_path=args.project_file)


if __name__ == "__main__":
    main()
