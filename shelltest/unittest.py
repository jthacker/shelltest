from __future__ import absolute_import
import inspect
import logging
import os
import re
import unittest

from shelltest.shelltest import (ShellTestFileFinder, ShellTestParser,
                                 ShellTestRunner, ShellTestResultsFormatter)


log = logging.getLogger(__name__)

non_alphanum_pattern = re.compile(r'[^a-zA-Z\d]')

def canonical_name(path):
    """Convert a string to its canonical name
    Parameters
    ==========
    path : str
        path name to convert

    Returns
    =======
    A canonical path name for path. Any non-alphanumeric value is converted to an underscore
    """
    return non_alphanum_pattern.sub('_', path)


def get_class_name(path, root_path):
    return 'TestShell_' + canonical_name(os.path.relpath(path, root_path))


def get_test_name(test):
    return 'test_line_{}'.format(test.source.line_num)


def new_test_method(test):
    def test_func(self, test=test):
        r = next(ShellTestRunner([test]).run())
        msg = ShellTestResultsFormatter.format_result(r)
        self.assertTrue(r.status.success, msg)
    return test_func


class ShellTestCaseBase(unittest.TestCase):
    pass


def create_unittests(path, module=None):
    """Find unit tests in path and create classes on the calling module representing the test cases
    Parameters
    ==========
    path : str
        path to shell tests, relative to the calling file
    module : python module (supporting attributes .__file__ and .__dict__)
        module to add test cases to
        defaults to the module of the call site

    Each shell test file is converted to a test case with each command converted to a single test
    """
    if module is None:
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])

    mod_dict = module.__dict__
    dirname = os.path.dirname(module.__file__)
    tests_path = os.path.abspath(os.path.join(dirname, path))

    finder = ShellTestFileFinder(tests_path)
    parsers = [ShellTestParser(p) for p in finder.find_paths()]
    for p in parsers:
        cls_name = get_class_name(p.path, tests_path)
        cls_members = { get_test_name(test):new_test_method(test) for test in p.parse() }
        assert cls_name not in mod_dict, 'Duplicate class name created'
        log.debug('creating class %r with members %r', cls_name, cls_members)
        mod_dict[cls_name] = (type(cls_name, (ShellTestCaseBase,), cls_members))
