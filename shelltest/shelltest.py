from __future__ import print_function

from collections import defaultdict, namedtuple
import itertools
import logging
import os
from subprocess import Popen, PIPE


log = logging.getLogger(__name__)

ShellTest = namedtuple('ShellTest', ('command', 'expected_output', 'source'))
ShellTestSource = namedtuple('ShellTestSource', ('name', 'line_num'))
ShellTestResult = namedtuple('ShellTestResult',
                             ('test', 'actual_output', 'ret_code', 'success'))


class ShellTestConfig(object):
    prompt = '>'
    shell_test_exts = ('sh', 'shtest')


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
        self._paths = paths
        self._cfg = cfg or ShellTestConfig

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
        self._cfg = cfg or ShellTestConfig

    def parse(self):
        """Parser path for tests
        Returns
        =======
        An iterable of ShellTest's found
        """
        return [t for t in self._test_gen()]


class ShellTestRunner(object):
    """ShellTestRunner"""

    def __init__(self, tests):
        self.tests = tests

    def run_shell_test(self, shell_test, show_tests=False):
        """Run a single shell test
        Parameters
        ==========
        shell_test : ShellTest
            Shell test to run
        show_tests : bool
            Print shell tests as they are executed

        Returns
        =======
        The ShellTestResult of running shell_test
        """
        if show_tests:
            print('exec: {!r} ... '.format(shell_test.command), end='')
        p = Popen(shell_test.command, shell=True, stdout=PIPE)
        stdout, stderr = p.communicate()
        success = (shell_test.expected_output == stdout)
        if show_tests:
            result_str = 'passed' if success else 'failed'
            print(result_str)
        return ShellTestResult(shell_test, stdout, p.returncode, success)

    def run(self, show_tests=False):
        """Run tests
        Parameters
        ======
        show_tests : bool
            display tests as they are executed

        Returns
        =======
        An iterable of ShellTestResults
        """
        return [self.run_shell_test(test, show_tests) for test in self.tests]


class ShellTestResultsFormatter(object):
    """ShellTestResultsFormatter"""

    def __init__(self, results):
        self._results = results

    def failed_tests(self):
        for r in self._results:
            if not r.success:
                yield r

    def format(self):
        """Return a string of formatted results"""
        src_stats = defaultdict(list)
        for r in self._results:
            src_stats[r.test.source.name].append(r)

        out = []
        failed_cnt = 0
        for src, results in src_stats.iteritems():
            n = len(results)
            p = sum(1 for r in results if r.success)
            failed_cnt += n - p
            out.append('{} {} of {} ({:3.1f}%) passed'\
                       .format(src, p, n, 100 * p / float(n)))
            for r in filter(lambda r: not r.success, results):
                out.append(' failed: {!r}'.format(r.test.command))
                out.append('     actual: {!r}'.format(r.actual_output))
                out.append('   expected: {!r}'.format(r.test.expected_output))
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
