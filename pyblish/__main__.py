"""Pyblish package interface

This makes the Pyblish package into an executable, via cli.py

"""

from . import cli

if __name__ == '__main__':
    cli.main(obj={}, prog_name="pyblish")
