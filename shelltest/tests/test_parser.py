import tempfile
from StringIO import StringIO

import pytest

from shelltest.shelltest import (ShellTestParser, ShellTest,
                                 ShellTestSource, ShellTestConfig,
                                 is_escaped_newline)


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
        ShellTest('echo hello', 'hello\n', ShellTestSource(str(path), 1), cfg),
        ShellTest('echo $?', '0\n', ShellTestSource(str(path), 3), cfg)]


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
    file_like_obj = StringIO(script.file.read())
    p = ShellTestParser(file_like_obj)
    assert shell_tests(file_like_obj, cfg) == p.parse()


def test_header_config():
    fobj = StringIO(
        "#[sht] command_prompt = asdf\n"\
        "#[sht] ignore_trailing_whitespace = False")
    p = ShellTestParser(fobj)
    p.parse()
    assert p._cfg.command_prompt == 'asdf'
    assert p._cfg.ignore_trailing_whitespace == False

    fobj = StringIO(
        "#[sht] command_prompt = a b c d\n"\
        "#[sht] ignore_trailing_whitespace = true")
    p = ShellTestParser(fobj)
    p.parse()
    assert p._cfg.command_prompt == 'a b c d'
    assert p._cfg.ignore_trailing_whitespace == True


def test_ignore_comments():
    fobj = StringIO(
        "> # Ignore this line\n"\
        "> echo Dont ignore this line\n"\
        "Dont ignore this line\n"\
        "> echo Or this # line\n"\
        "Or this")
    p = ShellTestParser(fobj)
    tests = p.parse()
    assert len(tests) == 2


def test_command_shell_changed():
    fobj = StringIO(
        "#[sht] command_shell = bash -c\n"\
        "> echo $0\n"\
        "bash\n")
    p = ShellTestParser(fobj)
    tests = p.parse()
    assert tests[0].cfg.command_shell == 'bash -c'


def test_command_prompt_changed():
    fobj = StringIO(
        "#[sht] command_prompt = py>\n"\
        "#[sht] command_shell = python -c\n"\
        "py> print('hello')\n"\
        "hello")
    p = ShellTestParser(fobj)
    tests = p.parse()
    assert tests[0].cfg.command_prompt == 'py>'
    assert tests[0].command == "print('hello')"


def test_multiline_command():
    fobj = StringIO(
        "> echo line1\\\n"
        "line2\n"
        "line1line2")
    p = ShellTestParser(fobj)
    tests = p.parse()
    assert len(tests) == 1
    assert tests[0].command == "echo line1\\\nline2"


@pytest.mark.parametrize('line, expected', (
    ('line\n', False),
    ('line', False),
    ('line\\\n', True),
    ('line\\\\\n', False)))
def test_is_escaped_newline(line, expected):
    assert is_escaped_newline(line) == expected
