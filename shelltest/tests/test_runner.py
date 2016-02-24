import tempfile
import StringIO

import pytest

from shelltest.shelltest import ShellTest, ShellTestSource, ShellTestRunner


@pytest.fixture
def tests():
    return [ShellTest('echo hello', 'hello\n', ShellTestSource('', 0)),
            ShellTest('echo $?', '0\n', ShellTestSource('', 2))]


def test_run(tests):
    r = ShellTestRunner(tests)
    results = r.run()
    assert len(results) == 2
    assert results[0].success
    assert results[0].ret_code == 0
    assert results[0].test == tests[0]
    assert results[0].actual_output == tests[0].expected_output
    assert results[1].success
    assert results[1].ret_code == 0
    assert results[1].test == tests[1]
    assert results[1].actual_output == tests[1].expected_output
