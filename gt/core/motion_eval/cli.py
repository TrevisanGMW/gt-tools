"""
Motion Evaluation command line - runs a job JSON file in any host.

This file can be run directly by path, so it also works where "-m" is not available
(Blender runs scripts by path):

    mayapy motion_eval/cli.py job.json [files...]
    blender --background --factory-startup --python motion_eval/cli.py -- job.json [files...]
    python motion_eval/cli.py job.json            (motion sample files only)

Options (see runner.main): --result <path>, --host auto|maya|blender, --verbose.
Exit codes: 0 all passed or warned, 1 some failed or errored, 2 invalid job.
"""

import os
import sys


def main():
    """Puts the folder containing motion_eval on sys.path and runs runner.main.

    Returns:
        int: Exit code.
    """
    package_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if package_parent not in sys.path:
        sys.path.insert(0, package_parent)
    package_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    runner = __import__(f"{package_name}.runner", fromlist=["main"])
    return runner.main()


if __name__ == "__main__":
    sys.exit(main())
