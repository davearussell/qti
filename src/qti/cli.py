import argparse
from .app import Application


def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--json-file', default='images.json',
                        help="JSON image file to load")
    return parser.parse_args()


def main():
    options = parse_cmdline()
    Application(options.json_file).run()
