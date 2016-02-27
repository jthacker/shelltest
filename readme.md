[![Build Status](https://travis-ci.org/jthacker/shelltest.svg?branch=master)](https://travis-ci.org/jthacker/shelltest)

# shelltest: command line program tester
Shelltest is a simple and compact method for testing command line programs.
Tests are simple shell like scripts that check their output against the expected output.


## Install
```
$ pip install shelltest
```

## Usage
Example test file:
```
$ cat doc/examples/simple.sh
#!/usr/bin/env shelltest
> echo An example shell test file
An example shell test file
> echo $?
0
```

Running tests with shelltest command
```
$ shelltest doc/examples/simple.sh
doc/examples/simple.sh 2 of 2 (100.0%) passed
```

Running actual shell test files
```
$ ./doc/examples/simple.sh
./doc/examples/simple.sh 2 of 2 (100.0%) passed
```

Add --verbose to show actual test output
```
$ ./doc/examples/simple.sh --verbose
exec: 'echo An example shell test file' ... passed
exec: 'echo $?' ... passed
./doc/examples/simple.sh 2 of 2 (100.0%) passed
```

## Shelltest files
Shell test files can end in either .sh or .shtest
Each line starting with a '>' is considered a command and all text following it,
up to but not including the nex '>', is considered the expected output.
Each command is executed and the actual output is compared to the expected output.
If they do not match exactly then the test is considered to have failed.

### Configuration Options
The header of a script file can contain configuration options that affect all tests in that file.
Configuration options are of the format `#!! key = value`, with one per line and they must proceed test.
Available options:

| Option                       | Type    | Description                                   | Default |
| ---------------------------- | ------- | --------------------------------------------- | ------- |
| `command_prompt`             | string  | Command delimiter                             | >       |
| `ignore_trailing_whitespace` | boolean | Ignore trailing whitespace in expected output | true    |
| `shell_command`              | string  | Shell to run commands in                      | `sh -c` |



# TODO
* add error reporting that shows line numbers of the failing test
* add py.test, unittest, nose test runner support
* allow other types of comparison between actual and expected output
