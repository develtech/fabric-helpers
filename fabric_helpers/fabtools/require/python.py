"""
Python environments and packages
================================

This module provides high-level tools for using Python `virtual environments`_
and installing Python packages using the `pip`_ installer.

.. _virtual environments: http://www.virtualenv.org/
.. _pip: http://www.pip-installer.org/

"""
import re
from distutils.version import StrictVersion as V

from fabric.api import hide, run, settings
from fabric.utils import puts
from fabtools.require.python import package, pip


def is_pipenv_installed(version=None, pipenv_cmd='pipenv'):
    """
    Check if `pipenv`_ is installed.

    .. _pipenv: https://docs.pipenv.org
    """
    with settings(hide('running', 'warnings', 'stderr', 'stdout'), warn_only=True):
        res = run('%(pipenv_cmd)s --version 2>/dev/null' % locals())
        if res.failed:
            return False
        if version is None:
            return res.succeeded
        else:
            m = re.search(r'pipenv (?P<version>.*)', res)
            if m is None:
                return False
            installed = m.group('version')
            if V(installed) < V(version):
                puts(f'pipenv {installed} found (version >= {version} required)')
                return False
            else:
                return True


def install_pipenv(python_cmd='python3'):
    package('pipenv', python_cmd=python_cmd)


def pipenv(pipenv_cmd='pipenv', python_cmd='python3', use_sudo=True):
    """
    Require `pipenv`_ to be installed.

    If pipenv is not installed, or if a version older than *version*
    is installed, the latest version will be installed.

    .. _pipenv: https://docs.pipenv.org
    """
    pip(python_cmd, use_sudo)
    if not is_pipenv_installed(version=None, pipenv_cmd=pipenv_cmd):
        install_pipenv(python_cmd=python_cmd)


def is_poetry_installed(version=None, poetry_cmd='poetry'):
    """
    Check if `poetry`_ is installed.

    .. _poetry: https://python-poetry.org
    """
    with settings(hide('running', 'warnings', 'stderr', 'stdout'), warn_only=True):
        res = run('%(poetry_cmd)s --version 2>/dev/null' % locals())
        if res.failed:
            return False
        if version is None:
            return res.succeeded
        else:
            m = re.search(r'Poetry version (?P<version>.*)', res)
            if m is None:
                return False
            installed = m.group('version')
            if V(installed) < V(version):
                puts(f'poetry {installed} found (version >= {version} required)')
                return False
            else:
                return True


def install_poetry(python_cmd='python3'):
    package('poetry', python_cmd=python_cmd)


def poetry(poetry_cmd='poetry', python_cmd='python3', use_sudo=True):
    """
    Require `poetry`_ to be installed.

    If poetry is not installed, or if a version older than *version*
    is installed, the latest version will be installed.

    .. _poetry: https://python-poetry.org
    """
    pip(python_cmd, use_sudo)
    if not is_poetry_installed(version=None, poetry_cmd=poetry_cmd):
        install_poetry(python_cmd=python_cmd)
