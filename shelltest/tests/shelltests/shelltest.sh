#!/usr/bin/env shelltest
# self test shelltest
> shelltest --version 2>&1  # python module argparse prints --version to stderr in 2.7
shelltest (0.2.0)

> shelltest; echo $?
2

> shelltest --help
usage: shelltest [-h] [--debug] [--verbose] [--version] paths [paths ...]

shelltest runner

positional arguments:
  paths       shell test file paths

optional arguments:
  -h, --help  show this help message and exit
  --debug     enable verbose logging
  --verbose   show tests
  --version   show version


> shelltest simple.sh
simple.sh 4 of 4 (100.0%) passed
