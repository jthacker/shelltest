from __future__ import print_function

from collections import defaultdict, MutableMapping, namedtuple
import itertools
import logging
import os
import re
import shlex
from subprocess import Popen, PIPE


log = logging.getLogger(__name__)


ShellTest = namedtuple('ShellTest', ('command', 'expected_output', 'source', 'cfg'))

ShellTestSource = namedtuple('ShellTestSource', ('name', 'line_num'))

ShellTestResultStatus = namedtuple('ShellTestResult', ('success', 'output_verified', 'ret_code_verified'))

ShellTestResult = namedtuple('ShellTestResult',
                             ('test', 'actual_output', 'ret_code', 'status'))

ShellTestConfigOption = namedtuple('ShellTestConfigOption', 'name,default,editable,typ')


def opt(name, default, editable, typ):
    return ShellTestConfigOption(name, default, editable, typ)


class ShellTestOptionNotEditable(Exception):
    pass


def bool_typ(s):
    s = s.lower()
    if s == 'false':
        return False
    elif s == 'true':
        return True
    raise ValueError('invalid boolean value {!r}'.format(s))


class ShellTestConfig(MutableMapping):
    """ShellTestConfig"""

    def __init__(self, shell_test_cfg=None):
        cfg = (
            opt('command_prompt', '>', True, str),
            opt('shell_command', 'sh -c', True, str),
            opt('ignore_trailing_whitespace', True, True, bool_typ),
            opt('shell_test_exts', ('sh', 'shtest'), False, list))
        self.__dict__['_cfg'] = { op.name:op for op in cfg }
        self.__dict__['_vals'] = { op.name:op.default for op in cfg }
        if shell_test_cfg is not None:
            self.__dict__['_vals'] = dict(shell_test_cfg.iteritems())

    def copy(self):
        return ShellTestConfig(self)

    def __len__(self):
        return len(self._vals)

    def __iter__(self):
        return iter(self._vals)

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, val):
        self[key] = val

    def __getitem__(self, key):
        return self._vals[key]

    def __setitem__(self, key, val):
        op = self._cfg[key]
        if not op.editable:
            raise ShellTestOptionNotEditable('{!r} is not an editable option'.format(key))
        self._vals[key] = op.typ(val)

    def __delitem__(self, key):
        raise NotImplemented()


class ShellTestFileFinder(object):
    """ShellTestFinder searches for shell tests in directories"""

    def __init__(self, paths, cfg=None):
        """Initialize ShellTestFinder
        Parameters
        ==========
        paths : iterable of paths
            paths can contain either a link directly to a shell test or a directory
            containing shell tests
        cfg : ShellTestConfig
        """
        if isinstance(paths, basestring):
            paths = [paths]
        self._paths = paths
        self._cfg = cfg or ShellTestConfig()

    @classmethod
    def is_shelltest_file(cls, path, cfg):
        if os.path.isfile(path):
            # ext is everything from the last dot to the end
            _, ext = os.path.splitext(path)
            if ext[1:] in cfg.shell_test_exts:
                return True
        return False

    @classmethod
    def _find_paths(cls, path, cfg):
        """Generator of shell test files
        Parameters
        ==========
        path : str
            path to shell test file or directory
        cfg : ShellTestConfig

        Returns
        =======
        Generator of paths to shell test files
        """
        log.debug('searching %r', path)
        if os.path.isdir(path):
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    path = os.path.join(dirpath, filename)
                    if cls.is_shelltest_file(path, cfg):
                        yield path
        elif cls.is_shelltest_file(path, cfg):
            yield path

    def find_paths(self):
        """Generator of shell test file paths"""
        for path in self._paths:
            for file_path in self._find_paths(path, self._cfg):
                yield file_path


class TestConfig(object):
    def __init__(self, cmd, cmd_line_num, output, cfg):
        self.cmd = cmd
        self.cmd_line_num = cmd_line_num
        self.output = output
        self.cfg = cfg


class ParserFSM(object):
    _re_arg = re.compile(r'#!!\s*([a-zA-Z0-9_]+)\s*=\s*(.+?)\s*$')
    _re_cmt = re.compile(r'^\s*#.*$')

    def __init__(self, cfg):
        self._state = self._state_parse_header
        self._line = None
        self._line_num = None
        self._test = None
        self._cfg = cfg
        self._tests = []
        self._errors = []

    def _get_command(self, line):
        idx = line.find(self._cfg.command_prompt)
        # command found
        if idx == 0:
            return line[idx+1:].strip()
        return None

    def _test_finished(self):
        """finish any pending tests"""
        if self._test:
            self._tests.append(self._test)
            self._test = None

    def _parse_cmd(self):
        """Check if line contains a command"""
        cmd = self._get_command(self._line)
        if cmd:
            self._test_finished()
            # Commands that are just comments are not considered tests
            if not self._re_cmt.match(cmd):
                self._test = TestConfig(cmd, self._line_num, [], self._cfg.copy())
                return True
        return False

    def _parse_arg(self, match_start=False):
        matcher = self._re_arg.match if match_start else self._re_arg.search
        m = matcher(self._line)
        if m:
            return m.groups()

    def _state_parse_header(self):
        arg = self._parse_arg(match_start=True)
        if arg:
            key, val = arg
            self._cfg[key] = val
        elif self._parse_cmd():
            self._state = self._state_parse_cmd

    def _state_parse_cmd(self):
        if not self._parse_cmd() and self._test:
            self._test.output.append(self._line)

    def finalize(self):
        self._test_finished()

    def next_line(self, line, line_num):
        self._line = line
        self._line_num = line_num
        self._state()

    @property
    def tests(self):
        return self._tests

    @property
    def errors(self):
        return self._errors


class ShellTestParser(object):
    """ShellTesetParser read in a ShellTest file"""

    def _parse_args(self):
        """Parse configuration arguments"""

    def _test_gen(self):
        fsm = ParserFSM(self._cfg)
        for line_num, line in enumerate(self._fobj.readlines()):
            fsm.next_line(line, line_num)
        fsm.finalize()
        for test in fsm.tests:
            src = ShellTestSource(self._path, test.cmd_line_num)
            yield ShellTest(test.cmd, ''.join(test.output), src, test.cfg)

    def __init__(self, path, cfg=None):
        """Initialize a ShellTestParser
        Parameters
        ==========
        path : str or file like object
            path to file to read from or file like object to read from
        cfg : ShellTestConfig
            configuration object
        """
        if isinstance(path, basestring):
            fobj = open(path)
        else:
            fobj = path
        self._fobj = fobj
        self._path = str(path)
        self._cfg = cfg or ShellTestConfig()

    @property
    def path(self):
        return self._path

    def parse(self):
        """Parser path for tests
        Returns
        =======
        An iterable of ShellTest's found
        """
        return [t for t in self._test_gen()]


class ShellTestRunner(object):
    """ShellTestRunner"""

    def __init__(self, tests, cfg=None):
        self.tests = list(tests)
        self._cfg = cfg or ShellTestConfig()

    def check_output(self, expected_output, actual_output, cfg):
        """Compare actual to expected output, comparison depends on the configuration
        """
        if cfg.ignore_trailing_whitespace:
            N = len(actual_output)
            if len(expected_output) < N:
                return False
            head, tail = expected_output[:N], expected_output[N:]
            # tail should only be whitespace
            return (tail.strip() == '') and (head == actual_output)
        return (actual_output == expected_output)

    def get_status(self, test, actual_output, ret_code, cfg):
        """Get the status of the command running, compares actual to expected output and the return code
        Returns
        =======
        ShellTestResultStatus
        """
        rc_verified = (ret_code == 0)
        out_verified = self.check_output(test.expected_output, actual_output, cfg)
        return ShellTestResultStatus(rc_verified and out_verified, out_verified, rc_verified)

    def get_command(self, test):
        return shlex.split(self._cfg.shell_command) + [test.command]

    def execute(self, test):
        cwd = os.path.dirname(test.source.name)
        if not os.path.isdir(cwd):
            cwd = '.'
        p = Popen(self.get_command(test), shell=False, stdout=PIPE, cwd=cwd)
        actual_output, _ = p.communicate()
        return actual_output, p.returncode

    def run_test(self, test):
        """Run a single shell test
        Parameters
        ==========
        test : ShellTest
            Shell test to run

        Returns
        =======
        The ShellTestResult of running test
        """
        actual_output, ret_code = self.execute(test)
        status = self.get_status(test, actual_output, ret_code, self._cfg)
        return ShellTestResult(test, actual_output, ret_code, status)

    def run(self, show_tests=False):
        """Run tests
        Parameters
        ======
        show_tests : bool
            display tests as they are executed

        Returns
        =======
        A generator of ShellTestResults
        """
        for test in self.tests:
            if show_tests:
                print('exec: {!r} ... '.format(test.command), end='')
            res = self.run_test(test)
            if show_tests:
                print('passed' if res.status.success else 'failed')
            yield res


class ShellTestResultsFormatter(object):
    """ShellTestResultsFormatter"""

    def __init__(self, results):
        self._results = list(results)

    def failed_tests(self):
        for r in self._results:
            if not r.status.success:
                yield r

    @classmethod
    def format_result(cls, result):
        if result.status.success:
            return 'command completed successfully'
        reason = 'unexpected output' if result.status.ret_code_verified else 'non-zero return code'
        msg = (
            'Command failed due to {reason}',
            '     file: {path}:{line_num}',
            '      cmd: {cmd!r}',
            '   actual: {actual!r}',
            ' expected: {expect!r}',
            '  retcode: {rc}',
        )

        return '\n'.join(msg).format(reason=reason,
                                     cmd=result.test.command,
                                     expect=result.test.expected_output,
                                     actual=result.actual_output,
                                     rc=result.ret_code,
                                     path=result.test.source.name,
                                     line_num=result.test.source.line_num)

    def format(self):
        """Return a string of formatted results"""
        src_stats = defaultdict(list)
        for r in self._results:
            src_stats[r.test.source.name].append(r)
        out = []
        failed_cnt = 0
        for src, results in src_stats.iteritems():
            n = len(results)
            p = sum(1 for r in results if r.status.success)
            failed_cnt += n - p
            out.append('{} {} of {} ({:3.1f}%) passed'\
                       .format(src, p, n, 100 * p / float(n)))
            for r in filter(lambda r: not r.status.success, results):
                out.append(self.format_result(r))
        if failed_cnt:
            out.append('{} test(s) failed'.format(failed_cnt))
        return '\n'.join(out)


def run(paths, show_tests=False):
    finder = ShellTestFileFinder(paths)
    parsers = [ShellTestParser(p) for p in finder.find_paths()]
    tests = list(itertools.chain.from_iterable(p.parse() for p in parsers))
    runner = ShellTestRunner(tests)
    results = runner.run(show_tests)
    fmt = ShellTestResultsFormatter(results)
    return results, fmt, sum(1 for _ in fmt.failed_tests())
