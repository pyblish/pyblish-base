"""Pyblish package interface

This makes the Pyblish package into an executable, via cli.py

"""

import pyblish.cli

if __name__ == '__main__':
    pyblish.cli.main(obj={}, prog_name="pyblish")
