#!/usr/bin/env shelltest
# Shelltest example file
#
# Input lines start with a '>'
# All lines following are considered output
# Comment only lines at the beginning of a file are valid.
# However, after the first command (e.g. '>'), they must appear following a '>',
# otherwise they will be considered part of the output for the previous command.
# Each test is executed completely independently

> echo 1234
1234
> # Command output can be checked as follows
> echo $?
0
> # New lines are significant, the following test fails
> echo 1234
1234

> # The previous line needs to be removed for the test to pass
