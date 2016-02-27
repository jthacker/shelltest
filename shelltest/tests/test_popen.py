from subprocess import Popen, PIPE

import pytest


@pytest.mark.parametrize('cmd,output', (
    (r'''awk 'BEGIN { printf "%s\n", "asdf" }' ''', 'asdf\n'),
    (r'''awk 'BEGIN { printf "%s", "asdf" }' ''', 'asdf'),
))
def test_popen_with_shell_output(cmd, output):
    p = Popen(cmd, shell=True, stdout=PIPE)
    stdout, _ = p.communicate()
    assert output == stdout


def test_popen_output():
    p = Popen(['awk', r'BEGIN { printf "%s\n","1234" }'], shell=False, stdout=PIPE)
    stdout, _ = p.communicate()
    assert stdout == '1234\n'
