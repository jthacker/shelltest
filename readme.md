[![Build Status](https://travis-ci.org/jthacker/shelltest.svg?branch=master)](https://travis-ci.org/jthacker/shelltest)

# shelltest: command line program tester
Shelltest is a simple and compact method for testing command line programs.
Tests are simple shell like scripts a command prompt that executes a command and
its expected output. The `shelltest` utility compares the actual output of each
command to the expected output, failing tests where the do not match.

## Audience
While this tool can be used for shell based testing of tools written any language,
the target audience is python based projects that wish to test their build artifacts inside of the
standard unittest framework.
For a more full featured shell-based testing tool not specifically targetting python project,
see the [shelltestrunner project](https://github.com/simonmichael/shelltestrunner).

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

### Running tests with shelltest command
```bash
$ shelltest doc/examples/simple.sh
doc/examples/simple.sh 2 of 2 (100.0%) passed
```

### Running a shell test file
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

### Unittests
In a file that will be picked up by the projects test runner (e.g. nose, py.test),
place the following.
```python
from shelltest.unittest import create_unittests
create_unittests('doc/examples/')
```
`create_unittests` takes a path where shelltest files can be found.
One TestCase is created for each shelltest file and a test method for each test in the file.
The `path` argument is taken relative to the file that `create_unittests` appears in.

## Shelltest files
Shell test files can end in either .sh or .shtest
Each line starting with a '>' is considered a command and all text following it,
up to but not including the next '>', is considered the expected output.
Each command is executed and the actual output is compared to the expected output.
If they do not match exactly then the test is considered to have failed.

### Configuration Options
The header of a script file can contain configuration options that affect all tests in that file.
Configuration options are of the format `#[sht] key = value`, with one per line and they must proceed all tests.
See `doc/examples/configuration_options.sh` for an example.

#### Available options:

| Option                       | Type    | Description                                   | Default |
| ---------------------------- | ------- | --------------------------------------------- | ------- |
| `command_prompt`             | string  | Command delimiter                             | >       |
| `command_shell`              | string  | Shell to run commands in                      | sh -c   |
| `ignore_trailing_whitespace` | boolean | Ignore trailing whitespace in expected output | true    |

## TODO
* allow other types of comparison between actual and expected output
