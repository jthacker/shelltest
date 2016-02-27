[![Build Status](https://travis-ci.org/jthacker/shelltest.svg?branch=master)](https://travis-ci.org/jthacker/shelltest)

# shelltest: command line program tester
Shelltest is a simple and compact method for testing command line programs.
Tests are simple shell like scripts that check their output against the expected output.


## Install
```bash
$ pip install shelltest
```

## Usage
Example test file:
```bash
$ cat doc/examples/simple.sh
#!/usr/bin/env shelltest
> echo An example shell test file
An example shell test file
> echo $?
0
```

Running tests with shelltest command
```bash
$ shelltest doc/examples/simple.sh
doc/examples/simple.sh 2 of 2 (100.0%) passed
```

Running actual shell test files
```bash
$ ./doc/examples/simple.sh
./doc/examples/simple.sh 2 of 2 (100.0%) passed
```

Add --verbose to show actual test output
```bash
$ ./doc/examples/simple.sh --verbose
exec: 'echo An example shell test file' ... passed
exec: 'echo $?' ... passed
./doc/examples/simple.sh 2 of 2 (100.0%) passed
```

## UnitTest Usage
Shelltests can also be run within your python project.
In a file that will be picked up by the projects test runner (e.g. nose, py.test),
place the following.
```python
from shelltest.unittest import create_unittests
create_unittests('path/to/shell/tests')
```
`create_unittests` takes a path where shelltest files can be found.
It then creates one TestCase for each shelltest file and a test method for each test in the file.

## Shelltest files
Shell test files can end in either .sh or .shtest
Each line starting with a '>' is considered a command and all text following it,
up to but not including the next '>', is considered the expected output.
Each command is executed and the actual output is compared to the expected output.
If they do not match exactly then the test is considered to have failed.

### Configuration Options
The header of a script file can contain configuration options that affect all tests in that file.
Configuration options are of the format `#[sht] key = value`, with one per line and they must proceed test.
Available options:

| Option                       | Type    | Description                                   | Default |
| ---------------------------- | ------- | --------------------------------------------- | ------- |
| `command_prompt`             | string  | Command delimiter                             | >       |
| `command_shell`              | string  | Shell to run commands in                      | `sh -c` |
| `ignore_trailing_whitespace` | boolean | Ignore trailing whitespace in expected output | true    |



# TODO
* add error reporting that shows line numbers of the failing test
* allow other types of comparison between actual and expected output
