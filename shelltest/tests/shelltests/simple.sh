#!! command_shell = bash -c
> echo 1234
1234
> echo $?
0
> echo 1234
1234
> [[ "asdf" == "asdf" ]] && echo true || echo false
true
