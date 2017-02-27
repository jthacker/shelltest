from __future__ import absolute_import
import logging
import sys

from terseparse import Parser, Arg, Lazy
from shelltest import __version__
from shelltest.shelltest import run


log = logging.getLogger(__name__)

description = """shelltest runner"""
P = Parser("shelltest", description,
    Arg('--debug', 'enable verbose logging', action='store_true'),
    Arg('--verbose', 'show tests', action='store_true'),
    Arg('--show-output', 'show output from each test as it is run',
        action='store_true'),
    Arg('--version', 'show version', action='version',
        version='%(prog)s ({})'.format(__version__)),
    Arg('paths', 'shell test file paths', nargs='+', metavar='path'))


def main():
    parser, args = P.parse_args()
    if args.ns.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.basicConfig()
    results, fmt, failed_tests = run(args.ns.paths,
                                     show_tests=args.ns.verbose or args.ns.show_output,
                                     show_output=args.ns.show_output)
    print(fmt.format())
    if failed_tests:
        sys.exit(1)
