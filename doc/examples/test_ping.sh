#!/usr/bin/env shelltest
> ping -c 3 google.com &> /dev/null && echo $?
0
