from setuptools import setup
from shelltest import __version__

setup(name='shelltest',
      description='Shell tester',
      packages=['shelltest'],
      version=__version__,
      url='https://github.com/jthacker/shelltest',
      download_url='https://github.com/jthacker/shelltest/archive/v{}.tar.gz'.format(__version__),
      author='jthacker',
      author_email='thacker.jon@gmail.com',
      keywords=['shell', 'testing'],
      classifiers=[],
      install_requires=['terseparse'],
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      entry_points = {
          'console_scripts': [
              'shelltest=shelltest.cli:main'
          ]},
      long_description="""
How to Install
--------------

.. code:: bash

    pip install shelltest

""")
