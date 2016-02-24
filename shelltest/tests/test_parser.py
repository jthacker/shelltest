import tempfile
import StringIO

import pytest

from shelltest.shelltest import ShellTestParser, ShellTest, ShellTestSource


_script = """\
> echo hello
hello
> echo $?
0
"""
@pytest.fixture
def script():
    f = tempfile.NamedTemporaryFile()
    f.write(_script)
    f.seek(0)
    return f


def shell_tests(path):
    return [
        ShellTest('echo hello', 'hello\n', ShellTestSource(str(path), 0)),
        ShellTest('echo $?', '0\n', ShellTestSource(str(path), 2))]


def test_parser_path(script):
    p = ShellTestParser(script.name)
    assert shell_tests(script.name) == p.parse()


def test_parser_file(script):
    p = ShellTestParser(script.file)
    assert shell_tests(script.file) == p.parse()


def test_parser_stringio(script):
    file_like_obj = StringIO.StringIO(script.file.read())
    p = ShellTestParser(file_like_obj)
    assert shell_tests(file_like_obj) == p.parse()
