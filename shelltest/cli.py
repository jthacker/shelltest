from __future__ import absolute_import
import logging
import os
import sys

from terseparse import Parser, Arg, Lazy
from shelltest.shelltest import run


log = logging.getLogger(__name__)

cwd = lambda _: [os.path.curdir]

description = """shelltest runner"""
P = Parser("shelltest", description,
    Arg('--debug', 'enable verbose logging', action='store_true'),
    Arg('--verbose', 'show tests', action='store_true'),
    Arg('paths', 'shell test file paths', nargs='*', metavar='path', default=Lazy(cwd)))


def main():
    parser, args = P.parse_args()

    if args.ns.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.basicConfig()

    results, fmt, failed_tests = run(args.ns.paths, args.ns.verbose)
    print(fmt.format())
    if failed_tests:
        sys.exit(1)
