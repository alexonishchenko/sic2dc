from pathlib import Path

import argparse

from .src.config_compare import ConfigCompareBase
from .src.tools import load_yaml


def main():
    parser = argparse.ArgumentParser(
        prog='sic2dc',
        description='Simple indented config to dict compare.',
        epilog='',
    )
    parser.add_argument(
        '-c1',
        '--config-1',
        type=str,
        help=f"relative path to the first config.",
        required=True,
        metavar='\b',
    )
    parser.add_argument(
        '-c2',
        '--config-2',
        type=str,
        help=f"relative path to the second config.",
        required=True,
        metavar='\b',
    )
    parser.add_argument(
        '-s',
        '--settings',
        type=str,
        help=f"relative path to settings yaml.",
        required=True,
        metavar='\b',
    )
    parser.add_argument(
        '-f',
        '--filters',
        type=str,
        help=f"relative path to filters list yaml.",
        default='',
        metavar='\b',
    )
    parser.add_argument(
        '-c',
        '--cures',
        type=str,
        help=f"relative path to cures list yaml.",
        default='',
        metavar='\b',
    )
    parser.add_argument(
        '-g',
        '--no-color',
        type=bool,
        help=f"disable color.",
        default=False,
        metavar='\b',
    )

    args = parser.parse_args()

    file1 = Path(args.config_1)
    file2 = Path(args.config_2)

    file_settings = Path(args.settings)
    settings = load_yaml(str(file_settings.absolute()))

    if args.cures:
        file_cures = Path(args.cures)
        cures = load_yaml(str(file_cures.absolute()))
    else:
        cures = list()

    if args.filters:
        file_filters = Path(args.filters)
        filters = load_yaml(str(file_filters.absolute()))
    else:
        filters = list()

    cc = ConfigCompareBase(
        f1=str(file1.absolute()), f2=str(file2.absolute()), settings=settings, filters=filters, cures=cures
    )

    color = not args.no_color

    if cc.diff_dict:
        cc.dump(quiet=False, color=color)
    else:
        print(f"No diffs found.")


if __name__ == '__main__':
    main()
