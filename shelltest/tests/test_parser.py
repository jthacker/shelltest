import tempfile
from io import StringIO

import pytest

from shelltest.shelltest import (ShellTestParser, ShellTest,
                                 ShellTestSource, ShellTestConfig,
                                 is_escaped_newline)


_script = u"""\
> echo hello
hello
> echo $?
0
"""
@pytest.fixture
def script():
    f = tempfile.NamedTemporaryFile(mode='r+')
    f.write(_script)
    f.seek(0)
    return f


def shell_tests(path, cfg):
    return [
        ShellTest(u'echo hello', u'hello\n', ShellTestSource(str(path), 1), cfg),
        ShellTest(u'echo $?', u'0\n', ShellTestSource(str(path), 3), cfg)]


def test_parser_path(script):
    cfg = ShellTestConfig()
    p = ShellTestParser(script.name)
    assert shell_tests(script.name, cfg) == p.parse()


def test_parser_file(script):
    cfg = ShellTestConfig()
    p = ShellTestParser(script)
    assert shell_tests(script, cfg) == p.parse()


def test_parser_stringio(script):
    cfg = ShellTestConfig()
    fobj = StringIO(str(script.read()))
    p = ShellTestParser(fobj)
    assert shell_tests(fobj, cfg) == p.parse()


def test_header_config():
    fobj = StringIO(
        u"#[sht] command_prompt = asdf\n"\
        u"#[sht] ignore_trailing_whitespace = False")
    p = ShellTestParser(fobj)
    p.parse()
    assert p._cfg.command_prompt == 'asdf'
    assert p._cfg.ignore_trailing_whitespace == False

    fobj = StringIO(
        u"#[sht] command_prompt = a b c d\n"\
        u"#[sht] ignore_trailing_whitespace = true")
    p = ShellTestParser(fobj)
    p.parse()
    assert p._cfg.command_prompt == 'a b c d'
    assert p._cfg.ignore_trailing_whitespace == True


def test_ignore_comments():
    fobj = StringIO(
        u"> # Ignore this line\n"\
        u"> echo Dont ignore this line\n"\
        u"Dont ignore this line\n"\
        u"> echo Or this # line\n"\
        u"Or this")
    p = ShellTestParser(fobj)
    tests = p.parse()
    assert len(tests) == 2


def test_command_shell_changed():
    fobj = StringIO(
        u"#[sht] command_shell = bash -c\n"\
        u"> echo $0\n"\
        u"bash\n")
    p = ShellTestParser(fobj)
    tests = p.parse()
    assert tests[0].cfg.command_shell == 'bash -c'


def test_command_prompt_changed():
    fobj = StringIO(
        u"#[sht] command_prompt = py>\n"\
        u"#[sht] command_shell = python -c\n"\
        u"py> print('hello')\n"\
        u"hello")
    p = ShellTestParser(fobj)
    tests = p.parse()
    assert tests[0].cfg.command_prompt == u'py>'
    assert tests[0].command == u"print('hello')"


def test_multiline_command():
    fobj = StringIO(
        u"> echo line1\\\n"
        u"line2\n"
        u"line1line2")
    p = ShellTestParser(fobj)
    tests = p.parse()
    assert len(tests) == 1
    assert tests[0].command == u'echo line1\\\nline2'


@pytest.mark.parametrize(u'line, expected', (
    (u'line\n', False),
    (u'line', False),
    (u'line\\\n', True),
    (u'line\\\\\n', False)))
def test_is_escaped_newline(line, expected):
    assert is_escaped_newline(line) == expected
