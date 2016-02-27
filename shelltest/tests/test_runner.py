import os
import tempfile
import StringIO

import pytest

from shelltest.shelltest import ShellTest, ShellTestSource, ShellTestRunner, ShellTestConfig, ShellTestParser


def runner(tests):
    tests = [ShellTest(cmd, output, ShellTestSource('', 0), ShellTestConfig()) for cmd, output in tests]
    return ShellTestRunner(tests)


@pytest.mark.parametrize("cmd,output,ret_code,success", (
    ('echo hello', 'hello\n', 0, True),
    ('echo $?', '0\n', 0, True),
    ('awk \'BEGIN { printf "%s", "asdf" }\'', 'asdf', 0, True),
    ('exit 42', '', 42, False),
    ('echo asdf', 'asdf\n\n\n', 0, True),
))
def test_echo(cmd, output, ret_code, success):
    r = runner([(cmd, output)])
    res = next(r.run())
    assert res.ret_code == ret_code
    assert res.status.success == success
    assert res.test == r.tests[0]


def test_working_directory_is_scripts_directory():
    file_path = os.path.abspath(__file__)
    dir_path = os.path.dirname(file_path)
    expected = dir_path + '\n'
    cfg = ShellTestConfig()
    tests = [ShellTest("pwd", expected, ShellTestSource(file_path, 0), cfg)]
    r = next(ShellTestRunner(tests).run())
    assert r.status.success


def test_command_shell_changed():
    fobj = StringIO.StringIO(
    "#[sht] command_shell = bash -c\n"\
    "> echo $0\n"\
    "bash\n")
    p = ShellTestParser(fobj)
    tests = p.parse()
    r = next(ShellTestRunner(tests).run())
    assert r.actual_output == 'bash\n'
