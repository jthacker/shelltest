from setuptools import setup
from shelltest import __version__


_extras = {
    'test': [
        'pytest'
    ]
}


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
      extras_require=_extras,
      install_requires=[
          'terseparse',
          'future>=0.16.0'
      ],
      setup_requires=['pytest-runner'],
      tests_require=_extras['test'],
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
