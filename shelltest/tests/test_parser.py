import tempfile
import StringIO

import pytest

from shelltest.shelltest import ShellTestParser, ShellTest, ShellTestSource, ShellTestConfig


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


def shell_tests(path, cfg):
    return [
        ShellTest('echo hello', 'hello\n', ShellTestSource(str(path), 0), cfg),
        ShellTest('echo $?', '0\n', ShellTestSource(str(path), 2), cfg)]


def test_parser_path(script):
    cfg = ShellTestConfig()
    p = ShellTestParser(script.name)
    assert shell_tests(script.name, cfg) == p.parse()


def test_parser_file(script):
    cfg = ShellTestConfig()
    p = ShellTestParser(script.file)
    assert shell_tests(script.file, cfg) == p.parse()


def test_parser_stringio(script):
    cfg = ShellTestConfig()
    file_like_obj = StringIO.StringIO(script.file.read())
    p = ShellTestParser(file_like_obj)
    assert shell_tests(file_like_obj, cfg) == p.parse()


def test_header_config():
    fobj = StringIO.StringIO(
        "#!! command_prompt = asdf\n"\
        "#!! ignore_trailing_whitespace = False")
    p = ShellTestParser(fobj)
    p.parse()
    assert p._cfg.command_prompt == 'asdf'
    assert p._cfg.ignore_trailing_whitespace == False

    fobj = StringIO.StringIO(
        "#!! command_prompt = a b c d\n"\
        "#!! ignore_trailing_whitespace = true")
    p = ShellTestParser(fobj)
    p.parse()
    assert p._cfg.command_prompt == 'a b c d'
    assert p._cfg.ignore_trailing_whitespace == True


def test_ignore_comments():
    fobj = StringIO.StringIO(
        "> # Ignore this line\n"\
        "> echo Dont ignore this line\n"\
        "Dont ignore this line\n"\
        "> echo Or this # line\n"\
        "Or this")
    p = ShellTestParser(fobj)
    tests = p.parse()
    assert len(tests) == 2
