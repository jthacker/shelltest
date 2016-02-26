import tempfile
import StringIO

import pytest

from shelltest.shelltest import ShellTest, ShellTestSource, ShellTestRunner


def runner(tests):
    tests = [ShellTest(cmd, output, ShellTestSource('', 0)) for cmd, output in tests]
    return ShellTestRunner(tests)


@pytest.mark.parametrize("cmd,output,ret_code,success", (
    ('echo hello', 'hello\n', 0, True),
    ('echo $?', '0\n', 0, True),
    ('exit 42', '', 42, True)))
def test_echo(cmd, output, ret_code, success):
    r = runner([(cmd, output)])
    res = r.run()[0]
    assert res.success == success
    assert res.ret_code == ret_code
    assert res.test == r.tests[0]
    assert res.actual_output == output
