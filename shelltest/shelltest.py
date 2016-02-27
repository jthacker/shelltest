from __future__ import print_function

from collections import defaultdict, namedtuple
import itertools
import logging
import os
from subprocess import Popen, PIPE


log = logging.getLogger(__name__)

ShellTest = namedtuple('ShellTest', ('command', 'expected_output', 'source'))
ShellTestSource = namedtuple('ShellTestSource', ('name', 'line_num'))
ShellTestResultStatus = namedtuple('ShellTestResult', ('success', 'output_verified', 'ret_code_verified'))
ShellTestResult = namedtuple('ShellTestResult',
                             ('test', 'actual_output', 'ret_code', 'status'))


class ShellTestConfig(object):
    def __init__(self):
        # Prompt to indicate command input in a shell test file
        self.prompt = '>'

        # Shell test extensions to search for
        self.shell_test_exts = ('sh', 'shtest')

        # Ignore trailing whitespace in expected output
        self.ignore_trailing_whitespace = True


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


class ShellTestParser(object):
    """ShellTesetParser read in a ShellTest file"""

    def _test_gen(self):
        """Parse tests from a file like object given the specified configuration
        Returns
        =======
        Generator of ShellTests
        """
        cmd, src = None, None
        for line_num, line in enumerate(self._fobj.readlines()):
            idx = line.find(self._cfg.prompt)
            if idx == 0:
                if cmd:
                    yield ShellTest(cmd, ''.join(out), src)
                cmd = line[idx+1:].strip()
                src = ShellTestSource(self._path, line_num)
                out = []
            elif cmd:
                out.append(line)
        if cmd:
            yield ShellTest(cmd, ''.join(out), src)

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
        if cfg.ignore_trailing_whitespace:
            N = len(actual_output)
            if len(expected_output) < N:
                return False
            head, tail = expected_output[:N], expected_output[N:]
            # tail should only be whitespace
            return (tail.strip() == '') and (head == actual_output)
        return (actual_output == expected_output)

    def get_status(self, test, actual_output, ret_code, cfg):
        """Compare actual to expected output, comparison depends on the configuration
        """
        rc_verified = (ret_code == 0)
        out_verified = self.check_output(test.expected_output, actual_output, cfg)
        return ShellTestResultStatus(rc_verified and out_verified, out_verified, rc_verified)

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
        cwd = os.path.dirname(test.source.name)
        if not os.path.isdir(cwd):
            cwd = '.'
        p = Popen(test.command, shell=True, stdout=PIPE, cwd=cwd)
        actual_output, _ = p.communicate()
        ret_code = p.returncode
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
        reason = 'non-zero return code' if result.status.ret_code_verified else 'unexpected output'
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
